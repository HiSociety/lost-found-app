# Lost and Found Document Recovery Platform

A web application built with Flask to help users recover lost National IDs and Passports by connecting with people who have found them.

## Features

- User authentication (login/register)
- Post lost documents with images
- Search for lost documents by ID or name
- Secure contact information sharing
- Document claim system
- Mobile-responsive design

## Tech Stack

- Python 3.8+
- Flask
- SQLAlchemy
- Bootstrap 5
- Font Awesome
- JavaScript (ES6+)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lost-found-app.git
cd lost-found-app
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
lost-found-app/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── static/            # Static files
│   ├── css/          # CSS styles
│   ├── js/           # JavaScript files
│   └── uploads/      # User uploaded images
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── home.html     # Home page
│   ├── login.html    # Login page
│   ├── register.html # Registration page
│   ├── post_item.html # Post document page
│   └── search.html   # Search page
└── instance/         # Instance-specific files
    └── lost_found.db # SQLite database
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 