from pydantic import BaseModel


class ReporteConsolidado(BaseModel):
    empresa: str
    periodo: str
    cpu_avg_aws: float = 0.0
    netout_gb_aws: float = 0.0
    cpu_avg_gcp: float = 0.0
    netout_gb_gcp: float = 0.0
    costo_aws: float = 0.0
    costo_gcp: float = 0.0
    costo_total: float = 0.0
    hash: str = ""
    generado_en: str = ""
