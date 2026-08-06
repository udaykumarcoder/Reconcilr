from __future__ import annotations
import pandas as pd
from pathlib import Path
import functools
import time
import logging
from contextlib import contextmanager
from typing import Iterator,Callable,TypeVar,Generator
from src.config import SourceConfig
from src.exceptions import SourceReadError,SchemaMismatchError


logger=logging.getlogger("pipeline")

F=TypeVar("F",bound=Callable)

def retry(times:int=3,delay:float=1.0)-> Callable[[F],F]:
    def decorator(func:F)->F:
        @functools.wrap(func)
        def wrapper(*args,**kwargs):
            last_exc:Exception | None = None
            for attempt in range(1,times+1):
                try:
                    return func(*args,**kwargs)
                except Exception as exc:
                    last_exc=exc
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s",attempt,times,func.__name__,exc
                    )
                    if attempt<times:
                        time.sleep(delay)

            raise SourceReadError(f"{func.__name__} failed after {times} attempts") from last_exc
        return wrapper
    return decorator

@contextmanager
def open_source(name:str)->Generator[None,None,None]:
    start=time.perf_counter()
    logger.info("Reading Source '%s'...",name)
    try:
        yield
    finally:
        elapsed=time.perf_counter()-start
        logger.info("Finished '%s' in %.3fs",name,elapsed)

def read_in_chunks(path:Path, chunk_size:int)-> Iterator[pd.DataFrame]:
    """yield successive chunks of the csv"""
    yield from pd.read_csv(path,chunk_size=chunk_size)


# Base Adapter

class SourceAdapter:
    """base class read->validate->clean"""
    def __init__(self,config:SourceConfig, raw_dir: Path):
        self.config=config
        self.path=raw_dir/config.file_name 

    def _read_raw(self)-> pd.DataFrame:
        if not self.path.exists():
            raise SourceReadError(f"File not found: {self.path}")
        # Generator reads chunks lazily, but list() materializes them all.
        # Good for demonstrating chunked reading, not for reducing RAM usage.
        chunks=list(read_in_chunks(self.path,self.config.chunk_size))
        return pd.concat(chunks,ignore_index=True)
        # ignore_index=True tells pd.concat() to discard the original row indices of the chunks and create a fresh continuous index.
    
    def _validate_schema(self,df:pd.DataFrame)->None:
        missing=[c for c in self.config.required_columns if c not in df.columns]
        if missing:
            raise SchemaMismatchError(self.config.name,missing)

    def _clean(self,df:pd.DataFrame)-> pd.DataFrame:
        before=len(df)
        df=df.drop_duplicates() #it removes only when complete rows are identical not any one or two

        for col in self.config.date_columns:
            if col in df.columns:
                df[col]=pd.to_datetime(df[col],errors="coerce")#here error coerce if a particualr cant be converted to date time it doesnt stop whole pipeline just write NotaTime (Nat) annd continues

        obj_cols=df.select_dtypes(include="object").columns
        df[obj_cols]=df[obj_cols].apply(lambda s:s.str.strip() if s.dtype=="object" else s)

        after=len(df)
        if before!=after:
            logger.info("%s:dropped %d exact duplicate rows",self.config.name,before-after)
        return df

    def load(self)->pd.DataFrame:
        with open_source(self.config.name):
            df=self._read_raw()
            self._validate_schema(df)
            df=self._clean(df)
        return df



# per source subclasses which only need extra logic

class OrdersAdapter(SourceAdapter):
    def _clean(self,df:pd.DataFrame)->pd.DataFrame:
        df=super()._clean(df)
        valid_statuses={"delivered","shipped","invoiced","processing","canceled"}
        df=df[df["order_status"].isin(valid_statuses)]
        return df


class OrderItemsAdapter(SourceAdapter):
    def _clean(self,df:pd.DataFrame)->pd.DataFrame:
        df=super()._clean(df)
        df["price"]=df["price"].fillna(0).clip(lower=0)
        df["freight_value"]=df["freight_value"].fillna(0)
        return df 

class PaymentsAdapter(SourceAdapter):
    def _clean(self,df:pd.DataFrame)->pd.DataFrame:
        df=super()._clean(df)
        df["payment_value"] = df["payment_value"].fillna(0).clip(lower=0)
        return df

class CustomersAdapter(SourceAdapter):
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super()._clean(df)
        df["customer_city"] = df["customer_city"].fillna("unknown").str.lower()
        df["customer_state"] = df["customer_state"].fillna("unknown").str.upper()
        return df

class ProductsAdapter(SourceAdapter):
    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super()._clean(df)
        df["product_category_name"] = df["product_category_name"].fillna("uncategorized")
        return df

ADAPTER_BY_SOURCE_NAME:dict[str,type[SourceAdapter]]={
    "orders":OrdersAdapter,
    "order_items": OrderItemsAdapter,
    "payments": PaymentsAdapter,
    "customers": CustomersAdapter,
    "products": ProductsAdapter,
}