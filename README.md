<!-- A basic project description and setup guide. -->

# Twin Health AI Assistant
- This is an intelligent chatbot powered by Gemini AI and built with Django is developed for Twin Health
- It is designed to classify SMS conversations into three main topics based on specific business rules:
1. *LAB*
2. *TWIN_APPOINTMENT*
3. *OTHERS*
- It utilizes a Retrieval-Augmented Generation (RAG) approach to handle contextual and rule-based classification.


## Features of Twin Health AI Assistant
- AI-powered conversations using Claude Sonnet 4
- Persistent conversation storage
- Beautiful modern UI with animations
- Session management
- Admin panel for managing conversations
- Quick reply buttons
- Chat history loading
- Responsive design


## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ashish1133/Balaji-twin-Health-.git
    cd Balaji-twin-Health-
    ```

2.  **Set up the Virtual Environment:**
    ```bash
    # Navigate to the project folder
    cd chatbot_project

    # Create virtual environment
    python -m venv .venv

    # Activate virtual environment
    # On Windows:
    .\.venv\Scripts\activate
    # On Linux/macOS:
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` inside the `chatbot_project/` directory:
    ```env
    SECRET_KEY=your-django-secret-key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1

    # LLM Configuration
    LLM_PROVIDER=Gemini
    GEMINI_API_KEY=your-google-gemini-api-key
    GEMINI_MODEL=gemini-2.5-flash
    ```

5.  **Run Migrations and Start Server:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

6.  **Access the App:**
    - Chat Interface: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
    - Admin Panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

7.  **Create Admin User (Optional):**
    To access the admin panel, create a superuser:
    ```bash
    python manage.py createsuperuser
    ```

The application will be accessible at `http://127.0.0.1:8000/`.

## Admin Panel
Visit http://127.0.0.1:8000/admin/ to manage conversations and messages.

## License
MIT License
