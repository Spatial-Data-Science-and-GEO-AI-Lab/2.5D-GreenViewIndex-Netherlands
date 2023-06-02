## Progress

| Week | Progress |
| ---- | -------- |
| Week 1 | - read relevant literature <br> - two relevant papers, among others: <br> 1) Modelling and mapping eye-level greenness visibility exposure using multi-source data at high spatial resolutions by S.M. Labib, Jonny J. Huck, Sarah Lindley <br> 2) Viewshed-based modelling of visual exposure to urban greenery – An efficient GIS tool for practical planning applications by Zofie Cimburova, Stefan Blumentrath |
| Week 2 | - familiarized myself with the calculation of viewshed analysis, decay model, GVI, among others <br> - coded viewshed using python for Utrecht area <br> - duplicated the code using R|
| Week 3 |  - switched to a sample of Amsterdam area due to missing data around Utrecht <br> - created a mask of Amsterdam streets to exclude points outside of street network from the analysis <br> - used Labib's function to run the GVI on a small part of Amsterdam <br> - replicated the GVI in R <br> - created a mask for buildings instead of streets and replicate the analysis <br> - collected income data on buurts (neighbourhoods) for the entire Netherlands from CBS <br> - used parallelization to run the analysis for the entire Amsterdam area  <br>
| Week 4 | - sampled  points 50m apart on linestrings street data from OSM <br>  - coded a pipeline to get new data from AHN3 on DSM and DTM (both 0.5m or 5m available) <br> - scaled up and calculated GVI for four cities Rotterdam, Hague, Utrecht and Amsterdam. <br> - Created tiles of streets of the Netherlands in order to be able to download data on the entire country <br>
| Week 5 | - Downloaded street data on the entire Netherlands using osmextract<br> - Coded a function that splits raster files into tiles to avoid memory issues with GVI <br> - Also, coded a function to split the street data into tiles <br> - Stored the tile files locally, looped through them to calculate GVI, and finally attached the results to a gdf <br>
| Week 6 | - investigated the feasibility of improving the DSM and DTM files <br> calculated a percentage of missing values on a sampled region from the streets (<5%) <br> in process - percentage of missing values for the entire netherlands <br> in process - obtain GVI for the entire Netherlands 
| Week 7 | |
| Week 8 | |
