### AI mood analyzer with explanations and recommendations
Is a simple and accessible web interface in which the user can enter text describing his current state (for example, a diary entry). The system analyzes the emotional coloring of the text, makes its decision and offers personalized recommendations.

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```
### 2. Start the FastAPI Backend

```bash
uvicorn backend.main:app --reload
```
### 3. Start the Streamlit Frontend

```bash
streamlit run frontend/app.py
