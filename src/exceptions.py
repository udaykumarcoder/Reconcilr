class PipelineError(Exception):
    """base class exception for all pipeline error"""

class SourceReadError(PipelineError):
    """Raised when a source file cant be read """

class SchemaMismatchError(PipelineError):
    """Raised when a data missing unexpected column missing columns"""
    def __init__(self,source_name:str,missing_columns:list[str]):
        self.source_name=source_name
        self.missing_columns=missing_columns
        super().__init__(
            f"Source '{source_name} is missing required columns: {missing_columns}'"
        )

class DuplicateKeyError(PipelineError):
    """Raised when a source has duplicate key values that couldnt be safely resolved"""
    def __init__(self,source_name:str,key_column:str,count:int):
        super().__init__(
         f"Source {source_name} keycolumn {key_column} count :{count}"   
        )