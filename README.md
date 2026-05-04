# Orders Master Infoprex

Sell Out & Orders Consolidation dashboard built with Streamlit. Consolidates sales data from multiple sources into a unified view for analysis and reporting.

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd Orders_Master_SDD
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Linux/Mac
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```bash
   streamlit run app.py
   ```
