# SmartLMS — Frontend Application (React + Vite)

## 1. Overview
The web client for SmartLMS (Teacher Assistance System) built with React 18, Vite, and modern JavaScript/CSS.

## 2. Directory Structure
```text
frontend/
├── public/               # Static assets
├── src/                  # Source code
│   ├── assets/           # Images, icons, and styling assets
│   ├── components/       # Reusable UI components
│   ├── pages/            # View pages / routes
│   ├── services/         # API clients and HTTP services
│   ├── App.jsx           # Root application component
│   ├── main.jsx          # React DOM entrypoint
│   └── index.css         # Global design system & styles
├── index.html            # HTML entrypoint
├── package.json          # Node dependencies & scripts
├── vite.config.js        # Vite configuration & proxy
├── .env.example          # Sample environment variables
└── README.md
```

## 3. Setup & Running Locally

### Prerequisites
- Node.js 18+
- npm or yarn

### Steps
1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

   The app will run at `http://localhost:3000` and proxy `/api` calls to `http://localhost:8000`.

3. Build for production:
   ```bash
   npm run build
   ```
