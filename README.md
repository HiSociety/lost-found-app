# Lost & Found Web Application

A web application that helps people find and return lost documents. Built with Flask and modern web technologies.

## 🌟 Features

- **Document Management**
  - Post lost documents
  - Search for found documents
  - Secure document verification
  - Image upload support

- **User Features**
  - User authentication
  - Profile management
  - Document tracking
  - Community testimonials

- **Admin Features**
  - Admin dashboard
  - User management
  - Document verification
  - System statistics

## 🚀 Tech Stack

- **Backend**: Python/Flask
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Email**: Flask-Mail
- **Security**: Flask-Limiter, CSRF Protection

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/HiSociety/lost-found-app.git
   cd lost-found-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Create an admin user:
   ```bash
   python create_admin.py
   ```

## 🏃‍♂️ Running the Application

1. Start the development server:
   ```bash
   flask run
   ```

2. Access the application at `http://localhost:5002`

## 📚 Documentation

Detailed documentation is available in the `docs` directory:
- [User Guide](docs/user_guide.md)
- [Admin Guide](docs/admin_guide.md)
- [API Documentation](docs/api_documentation.md)
- [Deployment Guide](docs/deployment_guide.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Thanks to all contributors
- Inspired by the need for a better way to handle lost documents

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers. 