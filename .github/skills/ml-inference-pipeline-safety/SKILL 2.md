---
name: ml-inference-pipeline-safety
description: Reglas de ingeniería para desplegar modelos de Machine Learning (Scikit-Learn, XGBoost, LightGBM) en pipelines productivos de datos o APIs (FastAPI/Dagster): prohibición absoluta de fit_transform en inferencia, serialización de Pipeline completo con joblib y validación de contrato de features.
---

# Machine Learning Inference Pipeline Safety

## Cuándo Activar esta Skill
- Al integrar un modelo de Machine Learning entrenado en notebooks dentro de un pipeline productivo (**Dagster, Airflow, FastAPI, batch scoring sobre DuckDB/Parquet**).
- Al revisar código de preprocesamiento (`StandardScaler`, `MinMaxScaler`, `OneHotEncoder`, `SimpleImputer`) para prevenir *Data Leakage* inverso o deriva silenciosa en inferencia.

## 1. Regla Inquebrantable: Prohibido `fit()` o `fit_transform()` en Producción

**Defecto Crítico Común**:
```python
# INCORRECTO EN PRODUCCIÓN / INFERENCIA
scaler = StandardScaler()
X_prod_scaled = scaler.fit_transform(X_prod)  # Recalcula media/desviación sobre el lote entrante!
```
- Si en inferencia llega 1 sola fila, `fit_transform` deja todas las variables en `0.0`; si llega un lote, destruye la escala original con la que aprendieron los pesos del modelo.

## 2. Patrón Estándar: Serialización de `sklearn.pipeline.Pipeline` Completo

Empaqueta siempre todas las transformaciones y el estimador final en un único objeto `Pipeline` durante el entrenamiento:

```python
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# 1. En Entrenamiento (único lugar donde se llama a .fit)
 numeric_cols = ["amount_cents", "tx_count_30d"]
cat_cols = ["channel_code"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ]
)

model_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression()),
    ]
)

model_pipeline.fit(X_train, y_train)
joblib.dump(model_pipeline, "artifacts/fraud_pipeline_v1.joblib")
```

## 3. Compuerta de Contrato de Features Antes de `.predict()`

En el asset de inferencia productiva, valida siempre el contrato de entrada antes de invocar `model_pipeline.predict(X_input)`:
1. Las columnas esperadas (`expected_features`) están todas presentes y en el tipo numérico/categórico correcto.
2. No hay valores `NaN` o `inf` no contemplados por un `SimpleImputer` dentro del `Pipeline`.
3. Registra la versión del artefacto (`model_version`, `sha256` del `.joblib`) en los metadatos de salida de la corrida.
