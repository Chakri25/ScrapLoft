import requests
from bs4 import BeautifulSoup
import re
import json
import mysql.connector as msc


page = requests.get("https://www.loft.com/")
main_link = "https://www.loft.com"

data = page.text
soup = BeautifulSoup(data,"html.parser")

category_links = {}
categories = soup.find_all('div',{'class': 'sub-nav-wrapper'})
for each in categories:
    for category in each.find_all('a'):
        category_links[category.get_text().strip()] = (main_link + category.get("href"))

dic = {}
sizeCodesDic = {}
colorCodesDic = {}
categoriesList = []
for category_name in category_links:
    category_name_ws = category_name.replace(" ","").replace("&","").replace("-","").replace(":","").replace(",","").lower()
    categoriesList.append(category_name_ws)

    if( ('must' in category_name_ws or 'most' in category_name_ws or 'guide' in category_name_ws or 'all' in category_name_ws
         or 'view' in category_name_ws or 'horoscopes' in category_name_ws or 'book' in category_name_ws or 'stories' in category_name_ws
         or 'new' in category_name_ws or 'sale' in category_name_ws) and category_name_ws != 'tall'):
        pass
        
    else:
        page = requests.get(category_links[category_name])
        data = page.text
        soup = BeautifulSoup(data, "html.parser")
        
        each_item_list = []
        for each in soup.find_all(attrs={"class":"product-wrap"}):
            detail_dic = {}
            try:
                pro_link = "https://www.loft.com"+each.a.get("href")
                item_page = requests.get(pro_link)
                item_data = item_page.text
                item_soup = BeautifulSoup(item_data, "html.parser")
                
                pro_id = item_soup.find(attrs={'name': 'productId'})['value']
                price = item_soup.find(attrs={'itemprop':'price'}).get_text()
                name = item_soup.find(attrs={'itemprop':'name'}).get_text()
               
                detail_dic["productId"] = pro_id
                detail_dic["productPrice"] = price
                detail_dic["productName"] = name
                
                if(pro_id != ""):
                    #for images, sizes and colors
                    script_data = item_soup.find_all('script')
                    str_res = str(script_data)
                    pos = str_res.find("window.productSettings = ")+len("window.productSettings = ")
                    remaining_str = str_res[pos:]
                    find_colon_pos = remaining_str.find("};")
                    json_str = remaining_str[:find_colon_pos+1]  
                    json_obj = json.loads(json_str)
                    
                    #for sizes, colors and their codes 
                    sizes = json_obj['products'][0]['skusizes']['sizes']
                    dic_sizes_colors = {}
                    for s in sizes:
                        sizeCodesDic[s['sizeCode']] = s['sizeAbbr']
                        colors = s['skucolors']['colors']
                        color_list = []
                        for c in colors:
                            color_list.append({c['colorCode']: c['quantity']})
                            colorCodesDic[c['colorCode']] = c['colorName']
                        dic_sizes_colors[s['sizeCode']] = color_list
                    detail_dic["sizesColors"] = dic_sizes_colors
                    detail_dic["imageLink"] = json_obj['products'][0]['prodImageURL']
                each_item_list.append(detail_dic)
                print(detail_dic)
                print()
            except Exception as e:
                print("error", e , " at",pro_link)
                print("================================================")
        
        dic[category_name_ws] = each_item_list


#####################################################################
#MySQL connection
connection = msc.connect(user="root", password="cha25kriP", host="localhost", database="LoftDatabase3")
cursor = connection.cursor()

#sizes
for s in sizeCodesDic:
    inserting_sizes = "insert into Sizes(sizeCode, size) values('"+str(s)+"','"+sizeCodesDic[s]+"')"
    cursor.execute(inserting_sizes)

#colors
for c in colorCodesDic:
    inserting_colors = "insert into colors(colorCode, color) values('"+str(c)+"','"+colorCodesDic[c]+"')"
    cursor.execute(inserting_colors)

countCat = 0
catdic = {}
for category in dic:
    
        print(category)
        countCat += 1
        #category table
        catdic[category] = countCat
        insert_catTable = "insert into category(categoryId, category) values('"+str(countCat)+"','"+category+"')"
        cursor.execute(insert_catTable)
        
        for each_item in dic[category]:
            try:
                proNum_value = each_item["productId"]
                proName_value = each_item["productName"]
                proPrice_value = each_item["productPrice"]
                proImageLink_value = each_item["imageLink"]
                inserting_data = "insert into products(productId, Categoryid, Name, Price, ImageLink) values ('"+str(proNum_value)+"', '"+str(catdic[category])+"', '"+proName_value+"', '"+proPrice_value+"', '"\
                                 + proImageLink_value +"')"
                cursor.execute(inserting_data)
                print(proNum_value, category)
                
                #inserting sizes and colors into productsizesColors table 
                for size in each_item['sizesColors']:
                    for color in each_item['sizesColors'][size]:
                        for i in color:
                            inserting_sizes_colors = "insert into productSizesColors(productId, SizeCode, ColorCode, quantity) values ('"\
                                                 +str(proNum_value)+"', '"+str(size)+"', '"+str(i)+"','"+str(color[i])+"')"
                        cursor.execute(inserting_sizes_colors)
                        print(i)
            except Exception as e:
                print("error",e,category,proNum_value)
                print("==========================================")
    

connection.commit()
connection.close()
print("done")

