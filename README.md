# indobert-absa-restaurant-dashboard
## Overview

This repository contains a Flask-based web application for Aspect-Based Sentiment Analysis (ABSA) of Indonesian restaurant reviews.

The application integrates an IndoBERT-based ABSA model with a MySQL database and an interactive dashboard to support the analysis and visualization of customer reviews.

The system was developed as part of an undergraduate thesis on IndoBERT-based aspect-level sentiment analysis and interactive visualization of restaurant reviews.

## Objectives

The application is designed to:

- Analyze restaurant reviews at the aspect level.
- Identify whether a review mentions a predefined restaurant aspect.
- Classify the sentiment associated with the target aspect as negative, neutral, or positive.
- Store and manage review analysis results in a MySQL database.
- Present analysis results through an interactive dashboard.

## System Features

The application may include the following features, depending on the functions implemented in the published source code:

- **Review Input and Data Processing:** Process review data submitted to the application.
- **ABSA Prediction:** Perform aspect detection and sentiment classification using the integrated model.
- **Review Management:** Store and retrieve review records and their analysis results.
- **Interactive Dashboard:** Visualize aspect-level sentiment results.
- **Filtering and Analysis:** Explore results based on available aspect, sentiment, time, or data-batch filters.

## Aspect Categories

The application uses five predefined restaurant review aspects:

1. Food
2. Service
3. Price
4. Ambience
5. Location

For each review–aspect pair, the model predicts aspect presence and the corresponding sentiment.

## Model Integration

The application uses a trained IndoBERT-Base-P1 model based on the Sentence Pair Classification (SPC) approach.

The model performs two tasks:

1. **Aspect Detection:** Determines whether the target aspect is present in the review.
2. **Sentiment Classification:** Predicts negative, neutral, or positive sentiment for the target aspect.

The model is trained separately from this web application. Refer to the model training repository for the training notebook and experimental details.

**Model repository:** [Add the Hugging Face model URL after publication]

## Technology Stack

- **Python:** Application programming language
- **Flask:** Web application framework
- **Jinja2:** HTML templating
- **MySQL:** Relational database
- **PyTorch:** Model inference
- **Hugging Face Transformers:** Pretrained language model and tokenizer support
- **HTML, CSS, and JavaScript:** Web interface and dashboard components

Include only the technologies actually used in the published application.

## System Workflow

1. Review data is submitted or imported into the application.
2. The application processes the review according to the implemented preprocessing procedure.
3. The trained ABSA model analyzes the review against the predefined aspects.
4. The application stores the review and its analysis results in the database.
5. The dashboard displays the available analysis results for exploration and monitoring.

## Repository Structure

indobert-absa-restaurant-dashboard/
├── controllers/
├── data/
├── model_ai/
├── models/
├── services/
├── static/
├── templates/
├── utils/
├── app.py
├── create_user.py
├── database.py
├── package.json
├── package-lock.json
├── requirements.txt
├── test_model.py
├── .env.example
├── .gitignore
└── README.md

### Directory and File Description

| `controllers/` | Contains controller modules for handling application requests and coordinating application logic. |
| `data/` | Contains supporting data files used by the application, if applicable. |
| `model_ai/` | Contains AI model artifacts or related files used for model inference. |
| `models/` | Contains application model modules or data-related model definitions. |
| `services/` | Contains service modules for application operations and business logic. |
| `static/` | Contains static assets such as CSS, JavaScript, images, and other frontend resources. |
| `templates/` | Contains HTML templates rendered by Flask using Jinja2. |
| `utils/` | Contains utility functions and supporting modules. |
| `app.py` | Main entry point for the Flask application. |
| `create_user.py` | Script related to user creation or account initialization. |
| `database.py` | Contains database connection or database access logic. |
| `package.json` | Defines Node.js package metadata and scripts, if used by the project. |
| `package-lock.json` | Records the dependency tree for npm packages. |
| `requirements.txt` | Lists Python dependencies required by the application. |
| `test_model.py` | Contains model-related testing code. |

The descriptions above are based on the directory and file names. Their exact responsibilities should be confirmed by inspecting the source code.


## Requirements

Before running the application, prepare:

- Python and the required Python packages.
- A MySQL server and the required database schema.
- Access to the trained IndoBERT ABSA model and its required tokenizer/configuration files.
- The environment variables needed by the application.

Refer to `requirements.txt` for the dependencies used by the project.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd indobert-absa-restaurant-dashboard
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file or configure the environment variables required by the application.

Use `.env.example` as a reference if it is provided. Do not commit database passwords, secret keys, or other credentials to GitHub.

### 5. Configure the Database

Create the required MySQL database and tables according to the database schema or SQL scripts provided in this repository.

Update the local database connection settings before running the application.

### 6. Prepare the Trained Model

Obtain the trained model artifacts from the documented model repository or another authorized location.

Configure the application to load the correct model, tokenizer, and architecture. Ensure that the model-loading and inference code matches the published model implementation.

### 7. Run the Application

```bash
python app.py
```

Open the local address displayed by Flask in your browser. The default development address is commonly `http://127.0.0.1:5000`, unless the application is configured differently.

## Data Privacy

The original restaurant review dataset used in the research is not included in this repository due to privacy and confidentiality considerations.

Database credentials, private configuration files, and other sensitive information must not be published.

If sample data is provided, it should be appropriately authorized for distribution and must not expose confidential information.

## Model Evaluation

The model's reported evaluation results are documented in the model training repository and the associated research thesis.

This repository focuses on the web application implementation and integration of the trained model rather than the model training experiments.

## Limitations

- Prediction quality depends on the trained model and the input review text.
- The application uses predefined aspect categories.
- Results may differ for reviews from other restaurants or domains.
- Reproducing the research evaluation requires the corresponding dataset and experimental setup, which are not included here.
