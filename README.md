# Carbon Emission Research Visualizer 🌍
This project visualizes the most discussed research topics about carbon emissions across districts (latitude). Using scraped keyword data, we employ LDA (Latent Dirichlet Allocation) modeling and Typhoon API for topic prediction, providing insightful visualizations for carbon emission trends.

## Features
- **Keyword Analysis**: Extracts key topics from research data.<br>
- **LDA Modeling**: Clusters research topics for deeper insights.<br>
- **Interactive Visualization**: Displays topic distribution across districts by latitude.
## Tech Stack
- **Programming Language**: Python
- **Libraries**: Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, Gensim
- **API**: Typhoon API for topic name predictions
- **Data Format**: CSV
## Installation
1. Clone the repository:
```bash
git clone https://github.com/VizKey01/Datasci_project.git  
cd Datasci_project  
```
2. Install required libraries:
```bash
pip install -r requirements.txt  
```
## Usage
Place your scraped research keyword data in the ```data/``` folder as a CSV file.
Run the script for topic modeling and visualization:
```bash
python main.py  
```
## Output
- A graphical representation of carbon emission research topics by district latitude.
- CSV and JSON files of processed topic distributions.
## Contributing
Feel free to fork the repository, create a branch, and submit a pull request. Contributions are always welcome!
