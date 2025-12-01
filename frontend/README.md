# dbt Cloud Demo Automation - React Frontend

Modern React frontend for the dbt Cloud Demo Automation tool, styled to match the dbt Cloud UI.

## Features

- 🎨 **dbt Cloud-inspired UI** - Familiar interface matching dbt Cloud's design
- 📱 **Mobile Responsive** - Works seamlessly on all device sizes
- ⚡ **Fast & Modern** - Built with React, Vite, and Tailwind CSS
- 🎯 **Simple UX** - Intuitive workflow from setup to success

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Python backend running (see main README)

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to `http://localhost:8000`.

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client
│   ├── components/    # Reusable components
│   ├── contexts/      # React contexts (session management)
│   ├── pages/        # Page components
│   ├── App.jsx       # Main app component
│   └── main.jsx      # Entry point
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Pages

1. **Setup** (`/setup`) - Configure demo inputs and API credentials
2. **Review** (`/review`) - Review AI-generated scenario
3. **Files** (`/files`) - Preview generated dbt files
4. **Repository** (`/repository`) - GitHub repository created
5. **Provisioning** (`/provisioning`) - dbt Cloud provisioning status
6. **Success** (`/success`) - Final success page

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`. All API calls are handled through `src/api/client.js`.

## Styling

Uses Tailwind CSS with custom colors matching dbt Cloud:
- `dbt-orange` - Primary accent color
- `dbt-purple` - Secondary accent
- `dbt-teal` - Success/positive actions
- `dbt-green` - Success indicators
- `dbt-gray` - Neutral grays

## Mobile Responsiveness

The UI is fully responsive with:
- Collapsible sidebar on mobile
- Stacked layouts on small screens
- Touch-friendly buttons and inputs
- Optimized spacing for mobile

