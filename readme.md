# Pricelabs Assignment
## Question
Exercises: Using the hotel prices data for 2012-2016 in the attached CSV, can you

1. Create a visualization/chart that makes it easy to find if there are any year over year repeating patterns in the data?

2. Identify any outliers in the data visually and programmatically?

3. [Bonus: only attempt if time allows] Estimate the hotel prices for each day in Feb 2022?

## Answer

Note - The original csv file has been renamed to 'data.csv' in this repository.

1) Built a dashboard using plotly and dash to do year on year analysis and find any repeating patterns in the data.The code is the `app.py` file Steps to run the dashboard app -
    <ul>

    ```bash
    pip install -r requirements.txt
    ```
   

    ```bash
    python app.py
    ```
    </ul>  
    The app is deployed at https://pricelabs-dashboard.onrender.com/ ( might take some time to load due to free tier)

2) The `analysis.ipynb` notebook contains code and visualization for the outlier detection and removal

3) (<b> BONUS TASK </b>)The `forecast.ipynb` notebook contains the code for future forcasting using the given historical data. The results of the prediction of each day of Feb 2022 are in the `february_2022_forecast.csv` file.





