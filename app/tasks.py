import os
import pandas as pd
import json
from datetime import datetime
from sqlalchemy.orm import Session
from celery import shared_task
from .database import SessionLocal
from .models import Job, Transaction, JobSummary
from .services.llm import classify_transactions_batch, generate_narrative_summary

def safe_float(val):
    try:
        if pd.isna(val):
            return 0.0
        if isinstance(val, str):
            val = val.replace('$', '').replace(',', '').strip()
        return float(val)
    except:
        return 0.0

def safe_date(val):
    try:
        if pd.isna(val):
            return None
        dt = pd.to_datetime(val, dayfirst=True)
        return dt.date()
    except:
        return None

@shared_task(bind=True)
def process_job(self, job_id: str):
    db: Session = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return

    try:
        job.status = "processing"
        db.commit()

        # 1. Read CSV
        filepath = os.path.join("uploads", job.filename)
        df = pd.read_csv(filepath)
        
        job.row_count_raw = len(df)

        # 2. Data Cleaning
        df = df.drop_duplicates()
        
        df['date'] = df['date'].apply(safe_date)
        df['amount'] = df['amount'].apply(safe_float)
        
        df['status'] = df['status'].astype(str).str.upper().replace('NAN', None)
        df['currency'] = df['currency'].astype(str).str.upper().replace('NAN', None)
        
        df['category'] = df['category'].fillna('Uncategorised')
        df['category'] = df['category'].replace('nan', 'Uncategorised')

        job.row_count_clean = len(df)
        db.commit()

        # 3. Anomaly Detection
        medians = df.groupby('account_id')['amount'].median().to_dict()
        
        domestic_brands = ['SWIGGY', 'OLA', 'IRCTC', 'ZOMATO', 'JIO RECHARGE', 'FLIPKART', 'BOOKMYSHOW']
        
        transactions_to_insert = []
        for _, row in df.iterrows():
            txn = Transaction(
                job_id=job.id,
                txn_id=str(row.get('txn_id')) if pd.notna(row.get('txn_id')) else None,
                date=row.get('date'),
                merchant=str(row.get('merchant')) if pd.notna(row.get('merchant')) else None,
                amount=row.get('amount'),
                currency=str(row.get('currency')) if pd.notna(row.get('currency')) else None,
                status=str(row.get('status')) if pd.notna(row.get('status')) else None,
                category=str(row.get('category')) if pd.notna(row.get('category')) else None,
                account_id=str(row.get('account_id')) if pd.notna(row.get('account_id')) else None,
                notes=str(row.get('notes')) if pd.notna(row.get('notes')) else None
            )
            
            # Outlier Anomaly
            if txn.account_id in medians and medians[txn.account_id] > 0 and txn.amount > 3 * medians[txn.account_id]:
                txn.is_anomaly = True
                txn.anomaly_reason = "Amount exceeds 3x account median"
                
            # Currency Anomaly
            merchant_upper = str(txn.merchant).upper() if txn.merchant else ""
            if txn.currency == 'USD' and any(brand in merchant_upper for brand in domestic_brands):
                txn.is_anomaly = True
                txn.anomaly_reason = "USD used for domestic merchant"

            transactions_to_insert.append(txn)
            
        db.add_all(transactions_to_insert)
        db.commit()

        # 4. LLM Classification
        uncategorized = db.query(Transaction).filter(
            Transaction.job_id == job.id, 
            Transaction.category == 'Uncategorised'
        ).all()
        
        if uncategorized:
            batch_size = 50
            for i in range(0, len(uncategorized), batch_size):
                batch = uncategorized[i:i+batch_size]
                payload = [{"txn_id": str(t.id), "merchant": t.merchant, "amount": t.amount, "notes": t.notes} for t in batch]
                
                results = classify_transactions_batch(payload)
                
                if results:
                    result_map = {str(res.get('txn_id')): res.get('category') for res in results}
                    for t in batch:
                        t.llm_category = result_map.get(str(t.id))
                        t.llm_raw_response = json.dumps(results)
                        if t.llm_category:
                            t.category = t.llm_category
                else:
                    for t in batch:
                        t.llm_failed = True
                        
                db.commit()

        # 5. Summary Generation
        all_txns = db.query(Transaction).filter(Transaction.job_id == job.id).all()
        total_inr = sum(t.amount for t in all_txns if t.currency == 'INR' and t.amount)
        total_usd = sum(t.amount for t in all_txns if t.currency == 'USD' and t.amount)
        anomaly_count = sum(1 for t in all_txns if t.is_anomaly)
        
        merchant_totals = {}
        for t in all_txns:
            if t.merchant and t.amount:
                merchant_totals[t.merchant] = merchant_totals.get(t.merchant, 0) + t.amount
        
        top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:3]
        top_merchants_list = [{"merchant": m, "amount": a} for m, a in top_merchants]
        
        summary_data = {
            "total_spend_inr": total_inr,
            "total_spend_usd": total_usd,
            "top_merchants": top_merchants_list,
            "anomaly_count": anomaly_count
        }
        
        narrative_res = generate_narrative_summary(summary_data)
        
        job_summary = JobSummary(
            job_id=job.id,
            total_spend_inr=total_inr,
            total_spend_usd=total_usd,
            top_merchants=top_merchants_list,
            anomaly_count=anomaly_count,
            narrative=narrative_res.get('narrative'),
            risk_level=narrative_res.get('risk_level')
        )
        db.add(job_summary)
        
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
