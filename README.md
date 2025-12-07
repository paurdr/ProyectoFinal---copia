📊 Dashboard Interactivo de Finanzas Personales

Este proyecto forma parte del Trabajo Final de la asignatura Desarrollo de Aplicaciones para la Visualización de Datos.
Su objetivo es ofrecer una herramienta interactiva y visual para analizar gastos, ingresos, categorías, instituciones, patrones financieros y predicciones mediante Machine Learning.

🚀 Cómo ejecutar la aplicación

Clona el repositorio.

Activa el entorno virtual o crea uno nuevo.

Instala las dependencias:

pip install -r requirements.txt


Ejecuta la aplicación desde el archivo principal:

python app.py


⚠️ Importante:
El archivo correcto para lanzar el dashboard es app.py.
El archivo app copia.py es únicamente una versión antigua que contiene el código completo previo a la limpieza y separación modular de los callbacks.

📁 Datos de entrada

El dashboard está preparado para funcionar con el archivo:

/Data/Data Transactions.xlsx


Este es el dataset que debe subirse desde la interfaz del dashboard para poder visualizar todos los análisis, gráficos y modelos.

🧩 Estructura del proyecto

app.py → Archivo principal. Contiene el layout del dashboard y carga los callbacks.

/callbacks/ → Módulos individuales con toda la lógica funcional.

/utils/ → Funciones auxiliares para carga, limpieza y preparación de datos.

/assets/style.css → Estilos personalizados (tema verde bosque + coral).

app copia.py → Copia completa del código previo a la organización.

/Data/Data Transactions.xlsx → Archivo de datos para cargar en el dashboard.
