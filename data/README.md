# Public example sources

## Iris

- File: `iris_uci.csv`; original UCI Iris records, 150 rows, no rows removed or corrected.
- Source: https://archive.ics.uci.edu/dataset/53/iris
- DOI: https://doi.org/10.24432/C56C76
- License: CC BY 4.0. Attribute the UCI Iris dataset when reusing the charts or data.
- SHA-256: `6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0`.
- Columns, units, transforms and chart contracts: `specs/iris_charts_v76.json`.

## Wine chemistry

- File: `wine_uci.data`; unchanged 178-row, 14-column UCI Wine file, with no rows removed or corrected.
- Source: https://archive.ics.uci.edu/dataset/109/wine ; raw file: https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data
- DOI: https://doi.org/10.24432/C5PC7J
- License: CC BY 4.0. Cite Aeberhard and Forina (1992), UCI Wine, when reusing the data or chart.
- SHA-256: `6be6b1203f3d51df0b553a70e57b8a723cd405683958204f96d23d7cd6aea659`.
- Source positions 0, 1 and 10 map to coded cultivar, alcohol and color intensity. UCI does not report physical units for the selected measurements; the chart discloses this on both axes. Coded cultivars are not named varieties.
- Data and chart contract: `specs/wine_charts_v76.json`; all 178 rows are plotted, with bounded display-only offsets for coincident positions.

## Quantitative-phase cell image

- File: `cell_scikit_image_v026.png`; unchanged scikit-image v0.26.0 `data.cell()` sample.
- Source documentation: https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.cell
- Pinned source file: https://raw.githubusercontent.com/scikit-image/scikit-image/v0.26.0/src/skimage/data/cell.png
- License: CC0. The source documentation cites Müller et al. (2018), DOI 10.1364/OE.26.010729.
- SHA-256: `8d23a7fb81f7cc877cd09f330357fc7f595651306e84e17252f6e0a1b3f61515`.
- Image dimensions: 550 × 660 pixels; documented spacing: 0.107 µm/pixel.
- The I01 panel uses the full original image, with no crop, stitch, LUT, gamma or intensity adjustment. Its histogram counts image pixels; it is not a biological-replicate analysis.
