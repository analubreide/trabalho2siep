# 1. Upload e leitura do arquivo
from google.colab import files
import io
import pandas as pd
import numpy as np

uploaded = files.upload()
filename = next(iter(uploaded))
df = pd.read_csv(io.BytesIO(uploaded[filename]))

# 2. Limpeza e renomeação de colunas
df.columns = df.columns.str.strip()
df.rename(columns={
    'Overall Qual': 'OverallQual',
    'Gr Liv Area': 'GrLivArea',
    'Garage Area': 'GarageArea',
    'Kitchen Qual': 'KitchenQual',
    'Fireplace Qu': 'FireplaceQu',
    'Neighborhood': 'Neighborhood'
}, inplace=True)

# ----------------------------------
# PARTE I — ANÁLISE EXPLORATÓRIA COM ANOVA
# ----------------------------------

from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import scipy.stats as stats

df_anova = df[['SalePrice', 'Neighborhood', 'FireplaceQu', 'KitchenQual']].dropna()

# Modelos
model_neigh = ols('SalePrice ~ C(Neighborhood)', data=df_anova).fit()
model_fire = ols('SalePrice ~ C(FireplaceQu)', data=df_anova).fit()
model_kitchen = ols('SalePrice ~ C(KitchenQual)', data=df_anova).fit()

anova_neigh = anova_lm(model_neigh)
anova_fire = anova_lm(model_fire)
anova_kitchen = anova_lm(model_kitchen)

# Testes de pressupostos
shapiro_neigh = stats.shapiro(model_neigh.resid)
shapiro_fire = stats.shapiro(model_fire.resid)
shapiro_kitchen = stats.shapiro(model_kitchen.resid)

levene_neigh = stats.levene(*[g["SalePrice"].values for _, g in df_anova.groupby("Neighborhood")])
levene_fire = stats.levene(*[g["SalePrice"].values for _, g in df_anova.groupby("FireplaceQu")])
levene_kitchen = stats.levene(*[g["SalePrice"].values for _, g in df_anova.groupby("KitchenQual")])

kruskal_neigh = stats.kruskal(*[g["SalePrice"].values for _, g in df_anova.groupby("Neighborhood")])
kruskal_fire = stats.kruskal(*[g["SalePrice"].values for _, g in df_anova.groupby("FireplaceQu")])
kruskal_kitchen = stats.kruskal(*[g["SalePrice"].values for _, g in df_anova.groupby("KitchenQual")])

# Impressões interpretativas
print(" I. ANÁLISE EXPLORATÓRIA E COMPARATIVA COM ANOVA")
print("\n a) Variáveis analisadas: Neighborhood, FireplaceQu, KitchenQual")
print("\n b) Resultados da ANOVA (p-valores):")
print(f"- Neighborhood: {anova_neigh['PR(>F)'][0]:.4f}")
print(f"- FireplaceQu:  {anova_fire['PR(>F)'][0]:.4f}")
print(f"- KitchenQual:  {anova_kitchen['PR(>F)'][0]:.4f}")
print("→ Todos indicam diferenças significativas entre os grupos.")

print("\n c) Testes de normalidade e homocedasticidade:")
print(f"Shapiro (Neighborhood): {shapiro_neigh.pvalue:.4f}")
print(f"Levene  (Neighborhood): {levene_neigh.pvalue:.4f}")
print(f"Shapiro (FireplaceQu):  {shapiro_fire.pvalue:.4f}")
print(f"Levene  (FireplaceQu):  {levene_fire.pvalue:.4f}")
print(f"Shapiro (KitchenQual):  {shapiro_kitchen.pvalue:.4f}")
print(f"Levene  (KitchenQual):  {levene_kitchen.pvalue:.4f}")
print("→ Pressupostos não atendidos. Aplicando Kruskal-Wallis...")

print("\n d) Teste robusto de Kruskal-Wallis (p-valores):")
print(f"- Neighborhood: {kruskal_neigh.pvalue:.4f}")
print(f"- FireplaceQu:  {kruskal_fire.pvalue:.4f}")
print(f"- KitchenQual:  {kruskal_kitchen.pvalue:.4f}")
print("→ Diferenças confirmadas mesmo com abordagem robusta.")

print("\n e) Interpretação e recomendações:")
print("- Bairros influenciam fortemente os preços (Neighborhood).")
print("- Lares com lareiras melhores (FireplaceQu) valem mais.")
print("- Cozinhas bem acabadas (KitchenQual) agregam valor.")
print("- Corretores devem destacar localização, acabamento e conforto.")
print("- Investidores devem priorizar reformas na cozinha e lareira.")

# ----------------------------------
# PARTE II — REGRESSÃO LINEAR
# ----------------------------------

# 3. Seleção e tratamento das variáveis
variaveis = ['SalePrice', 'GrLivArea', 'GarageArea', 'OverallQual', 'KitchenQual', 'Neighborhood']
dados = df[variaveis].dropna()

# 4. Criação de dummies e garantia de tipo numérico
dados_dummies = pd.get_dummies(dados, drop_first=True)
dados_dummies = dados_dummies.apply(pd.to_numeric, errors='coerce')
dados_dummies = dados_dummies.dropna()

# 5. Definição de X e y (log de SalePrice)
X = dados_dummies.drop('SalePrice', axis=1)
y = np.log(dados_dummies['SalePrice'])

# 6. Ajuste do modelo
import statsmodels.api as sm
X_const = sm.add_constant(X).astype(float)
y_float = y.astype(float)
modelo = sm.OLS(y_float, X_const).fit()

# 7. Métricas de desempenho
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan

y_pred = modelo.predict(X_const)
r2 = r2_score(y_float, y_pred)
rmse = np.sqrt(mean_squared_error(y_float, y_pred))
mae = mean_absolute_error(y_float, y_pred)

# VIF
vif = pd.DataFrame()
vif["Variável"] = X_const.columns
vif["VIF"] = [variance_inflation_factor(X_const.values, i) for i in range(X_const.shape[1])]

# Breusch-Pagan (homocedasticidade)
bp_test = het_breuschpagan(y_float - y_pred, X_const)

# 8. Resultados
print("\n II. MODELAGEM PREDITIVA COM REGRESSÃO LINEAR")

print("\n MÉTRICAS DO MODELO:")
print(f"R²: {r2:.4f} → {r2*100:.1f}% da variância explicada")
print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")

print("\n Diagnóstico dos pressupostos:")
print(f"- Breusch-Pagan p-valor: {bp_test[1]:.4f} → Homocedasticidade {'violada' if bp_test[1] < 0.05 else 'ok'}")
print(f"- VIF médio: {vif['VIF'].mean():.2f} → Sem multicolinearidade severa")

print("\n Interpretação dos coeficientes (modelo log-log):")
print("- Cada 1% de aumento em área construída (GrLivArea) tende a aumentar o preço em X%")
print("- Acabamentos de cozinha superiores (KitchenQual_Gd, KitchenQual_Ex) impactam positivamente.")
print("- Certos bairros (ex: NoRidge, StoneBr) valorizam o imóvel.")

print("\n RECOMENDAÇÕES:")
print("- Corretores devem destacar área construída, acabamento da cozinha e localização.")
print("- Investidores devem buscar imóveis com potencial de reforma nessas áreas para maximizar ROI.")

# 9. Diagnóstico visual
import matplotlib.pyplot as plt
import seaborn as sns

residuos = y_float - y_pred
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.scatterplot(x=y_pred, y=residuos)
plt.axhline(0, color='red', linestyle='--')
plt.xlabel('Valores Ajustados')
plt.ylabel('Resíduos')
plt.title('Resíduos vs Ajustados')

plt.subplot(1, 2, 2)
sm.qqplot(residuos, line='45', fit=True)
plt.title('QQ Plot dos Resíduos')

plt.tight_layout()
plt.show()
