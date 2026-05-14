# EONET East Africa Dashboard

A Python-based web dashboard for visualizing natural events across East Africa using data from NASA's [Earth Observatory Natural Event Tracker (EONET)](https://eonet.gsfc.nasa.gov/).

## Overview

This project fetches and displays real-time and historical natural event data (wildfires, floods, droughts, storms, etc.) from the EONET API, filtered and focused on the East Africa region.

## Features

- Interactive map visualization of natural events in East Africa
- Filtering by event category, date range, and status
- Integration with the NASA EONET v3 API

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/YonSci/eonet-east-africa.git
cd eonet-east-africa
pip install -r requirements.txt
```

### Running the App

```bash
python app.py
```

Then open your browser at `http://localhost:8050` (or the configured port).

## Data Source

Natural event data is sourced from the [NASA EONET API v3](https://eonet.gsfc.nasa.gov/docs/v3).

## License

MIT
