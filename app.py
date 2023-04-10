from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

playstore27 = pd.read_csv('data/googleplaystore.csv')
playstore27.drop_duplicates(subset = ['App'],keep='first',inplace=True) 

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore27.drop([10472], inplace=True)

playstore27['Category']=playstore27['Category'].astype('category')

playstore27['Installs'] = playstore27['Installs'].apply(lambda x: x.replace(',',''))
playstore27['Installs'] = playstore27['Installs'].apply(lambda x: x.replace('+',''))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore27['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore27['Size'] = (playstore27['Size'].replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore27['Size'].str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore27['Size'].fillna(playstore27.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore27['Price'] = playstore27['Price'].apply(lambda x: x.replace('$',''))
playstore27['Price'] = playstore27['Price'].astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore27[['Reviews','Size','Installs']]=playstore27[['Reviews','Size','Installs']].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore27.copy()

    # Statistik
    top_category1 = pd.crosstab(
        index=df2['Category'],
        columns='Jumlah').reset_index().sort_values(by='Jumlah',ascending=False).head()
    
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category1.iloc[0,0],
        'total': top_category1.iloc[0,1],
        'rev_table' : df2.groupby(by=['Category','App']).agg({'Reviews':'sum','Rating':'mean'}).sort_values(by='Reviews',ascending=False).reset_index().head(10).to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    ## Bar Plot
    cat_order = df2.groupby(by='Category').agg({'Category':'count'  }).rename({'Category':'Jumlah'}, axis=1).sort_values(by='Jumlah',ascending=False).head()
    X = cat_order.reset_index()['Category']
    Y = cat_order.reset_index()['Jumlah']
    my_colors = ['r','g','b','k','y','m','c']
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X,Y, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore27['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('reviews_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    dfputri=df2.copy()
    dfputri['Last Updated']=dfputri['Last Updated'].astype('Datetime64')
    dfputri['years']=dfputri['Last Updated'].dt.year
    dfputri
    cat_reviews=dfputri.groupby(by='years').agg({'Reviews':'mean'}).rename({'Reviews':'Total'},axis=1).sort_values(by='Total',ascending=False).head()
    X2=cat_reviews.reset_index()['years']
    Y2=cat_reviews.reset_index()['Total']
    ai_colors = ['r','g','b','k','y','m','c']
    fig=plt.figure(figsize=(5,5),dpi=300)
    fig.add_subplot()
    plt.barh(X2,Y2, color=ai_colors)
    plt.xlabel('Average Reviews')
    plt.ylabel('years')
    plt.savefig('cat_reviews.png',bbox_inches='tight')

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]
    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3,result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)
