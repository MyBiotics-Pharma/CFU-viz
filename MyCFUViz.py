# %%
import pandas as pd
import plotly.express as px 
import numpy as np
from io import BytesIO
import streamlit as st
from PIL import Image
# %%
st.set_page_config(layout="wide",page_title="MyCFUViz",page_icon=Image.open("fav.ico"))
pd.options.display.float_format = '{:,.2f}'.format
# hide_streamlit_style = """
#               <style>
#               footer {visibility: hidden;}
#               [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
#                      width: 500px;
#                      }
#               [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
#                      width: 500px;
#                      margin-left: -500px;
#                      }
#             </style>
#             """
            
            

hide_streamlit_style = """
              <style>
              #MainMenu {visibility: hidden;}
              footer {visibility: hidden;}
              [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
                     width: 500px;
                     }
              [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
                     width: 500px;
                     margin-left: -500px;
                     }
            </style>
            """            
            
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


# %%
y_variables=["Normalized_Count_1","Normalized_Count_2","Normalized_Count_3","Normalized_Count_4","Normalized_Count_5"]
ignore_list=['Count_1','Count_2','Count_3','Count_4','Count_5','Average','LOG','STD','Average Dilutions','Average STD']

default_dict={
                     'color':None,
                     'facet':None,
                     'height':500,
                     'names':"Average_by",
                     'boxwidth':0.8,
                     'points':False,
                     'log':True,
                     'remove_zero':True,
                     'start_at_one':False,
                     'font_size':14,
                     'xlabels':True,
                     'ref_line':False
                     }
       
def st_header_section():
       # Set up header section of app
       head=st.columns(3)
       head[0]=head[2]=st.write("")
       head[1].image("Mybiotics_LOGO - Large.png",width=350)
       st.title("MyCFUViz")


def st_template_download():
       # Set up template download section
       download_column=st.container()
       download_column.subheader("Template to use for the app")
       with open('Template_CFU.xlsx','rb') as f:
              download_column.download_button('Click Me to Download Template XLSX File',f,file_name='Template.xlsx')
       download_column.text('Feel free to change the names of Sample Data columns or add new columns')
       download_column.text('Other columns should not be changed')
       # upload_data_widget=download_column.file_uploader(label='Upload File', type=['xlsx'],accept_multiple_files=True)

def st_file_upload_section():
       # Set up file upload section of app
       global upload_data_widget
       upload_column=st.container()
       upload_column.subheader("File Upload (use intended template)")
       upload_data_widget=upload_column.file_uploader(label='Upload File', type=['xlsx'],accept_multiple_files=True)


def st_data_section():
       global df
       # Set up section where data is shown
       st.subheader("DataFrames")
       data=st.expander('Raw DataFrame (Click to Show)')
       data.subheader("Raw Data")
       data_text=data.text("Loading data file...")
       df=excel_to_df(upload_data_widget)
       data.write(df.astype(str))
       data_text.text("Data file loaded")
def filter_data():
       # Filter data according to widgets
       global df_filtered, df_melt
       df_filtered=df.query(query[:-2])
       if remove_zero:
              df_filtered[y_variables]=df_filtered[y_variables].replace(0,np.nan)
       else:
              df_filtered[y_variables]=df_filtered[y_variables].replace(0,1.00001)
       df_filtered['custom_name']=df_filtered[names].astype(str).agg('/'.join, axis=1)
       df_melt=pd.melt(df_filtered,id_vars=[x for x in df_filtered.columns if x not in y_variables+ignore_list],value_vars=y_variables)
       
def st_filtered_data_section():
       
       # Set up section where filtered data is shown
       filtered_data=st.expander("Filtered DataFrame (Click to Show)")
       filtered_data.subheader('Filtered Data') 
       filtered_data.write(df_filtered.astype(str))


def st_plot_section():
       # Set up section where plots are shown
       st_figure=st.container()
       st_figure.subheader("Figures")
       st_figure.subheader("CFU Plot")
       show_metadata_on_hover=st_figure.checkbox("Show Metadata On Hover (When disabled - showing median/mean/min/max values)")
       df=df_filtered
       if color:
              df[color]=df[color].astype(str)
       fig=px.box(df,x='custom_name',y=y_variables,color=color,height=height,log_y=log,facet_col=facet)
       if log: 
              max_val=np.log10(df[y_variables].max().max())+0.5
              y_val=10**max_val
              min_val=np.log10(df[y_variables].min().min())-0.5
              if start_at_one:
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     # fig.layout.yaxis.autorange=True
                     fig.update_layout(yaxis_range=[min_val,max_val])
                     
       else:
              max_val=df[y_variables].max().max()*1.05
              y_val=max_val
              min_val=df[y_variables].min().min()*0.95
              if start_at_one:
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     fig.update_layout(yaxis_range=[min_val,max_val])
                     # fig.layout.yaxis.autorange=True
       fig.update_layout(font=dict(size=font_size,))      
       fig.update_xaxes(showticklabels=xlabels)
       fig.update_traces(width=boxwidth, boxmean=True)
       fig.update_xaxes(tickangle=90,matches=None,title=None,dtick=1,autorange=True)
       fig.update_yaxes(exponentformat='E')
       fig.update_layout(hovermode="x")
       if points:
            fig.update_traces(boxpoints='all',jitter=0.05)
       else:
            fig.update_traces(boxpoints=None)
       hover_plot = px.bar(df, x="custom_name", y=[y_val] * len(df["custom_name"]),
                                   barmode="overlay",hover_data=cols,facet_col=facet,log_y=log)
       hover_plot.update_traces(width=boxwidth, opacity=0,)             
       hover_plot.update_layout(yaxis_range=[0,max_val])
       if show_metadata_on_hover:
              fig.add_traces(hover_plot.data)
              # hover_plot.add_traces(fig.data)
              
              
       # fig.add_traces(fig.data)
       
       st_figure.plotly_chart(fig,use_container_width=True)
       # st_figure.plotly_chart(hover_plot,use_container_width=True)




def st_plot2_section():
       # Set up section where plots are shown
       st_figure2=st.container()
       st_figure2.subheader("Scatter")
       val_to_show_scatter=st_figure2.selectbox("Metric to show", options=['Mean','Median','Min','Max'])
       if val_to_show_scatter=='Min':
              metric='min'
       elif val_to_show_scatter=='Max':
              metric='max'
       elif val_to_show_scatter=='Median':
              metric='median'
       elif val_to_show_scatter=='Mean':
              metric='mean'
       df=df_melt.groupby(by=['custom_name']).agg(metric).reset_index()
       df_std=df_melt.groupby(by=['custom_name']).agg('sem')
   
       if color:
              df[color]=df[color].astype(str)
       
       fig=px.scatter(df,x='custom_name',y='value',color=color,height=height,log_y=log,facet_col=facet,error_y=df_std['value'])
       if log: 
              
              if start_at_one:
                     max_val=np.log10(df['value'].max())+0.5
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     fig.layout.yaxis.autorange=True
                     
       else:
              if start_at_one:
                     max_val=df['value'].max()*1.05
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     fig.layout.yaxis.autorange=True
                     
       
       fig.update_layout(font=dict(size=font_size,))       
       # fig.update_traces(width=boxwidth, boxmean=True)
       fig.update_xaxes(tickangle=90,matches=None,title=None,dtick=1,autorange=True)
       fig.update_yaxes(exponentformat='E')
       # if points:
       #      fig.update_traces(boxpoints='all')
       # else:
       #      fig.update_traces(boxpoints=None)
       
       

        
       with st.spinner(text="In progress..."):
              st_figure2.plotly_chart(fig,use_container_width=True)

def excel_to_df(upload_data_widget):
       # Get input: excel file
       # Return pandas df
       global cols, df
       if len(upload_data_widget)==1:
              df=pd.read_excel(BytesIO(
                    upload_data_widget[0].getvalue()), skiprows=1).round(3)
       elif len(upload_data_widget)>1:
              df=pd.read_excel(BytesIO(
                    upload_data_widget[0].getvalue()), skiprows=1).round(3)
              for file in upload_data_widget[1:]:
                     df=pd.concat([df,pd.read_excel(BytesIO(
                    file.getvalue()), skiprows=1).round(3)])
                     
       ind=list(df.columns).index('Plate')
       cols=df.columns.tolist()[:ind+1]
       df[cols] = df[cols].replace(np.nan, "")
       return df


def add_logo_and_links_to_sidebar():
       #Adds logo and links to the different sections in the sidebar
       st.sidebar.image("Mybiotics_LOGO - Large.png",width=250,)
       links=st.sidebar.container()
       links.subheader('Links')
       links.markdown("[File Upload](#file-upload)", unsafe_allow_html=True)
       links.markdown("[DataFrames](#dataframes)", unsafe_allow_html=True)
       # links.markdown("[Filtered Data](#filtered-data)", unsafe_allow_html=True)
       links.markdown("[Figures](#figures)", unsafe_allow_html=True)
       
       
def get_filters_and_add_widgets_to_sidebar(df):
       # Parse the df and get filter widgets based on columns
       
       global query, widget_dict
       widget_dict={}
       query=f""
       st.sidebar.header('Widgets',)
       filter_widgets=st.sidebar.expander("Data Filters. After choosing filters press the button at the bottom.")
       filter_widgets.subheader('Filter Data')
       form=filter_widgets.form('form1')
       
       if "Dilution" in df.columns:
              sample_data_col="Dilution"
       elif "CountedDilution" in df.columns:
              sample_data_col="CountedDilution"
       else:
              sample_data_col=df.columns[-1]
       
       
       for y in df.columns[1:df.columns.get_loc(sample_data_col)]:
              if len(df[y].unique().tolist())>1:
                     widget_dict[y]=form.multiselect(label=str(y),options=df[y].unique().tolist(),default=df[y].unique().tolist())    
                     query+=f"`{y}`  in {widget_dict[y]} & "
       form.form_submit_button("Fiter Data")
       
       
def add_plot_settings_to_sidebar():
       # Adds plot settings widget to sidebar
       global color, facet, height, names,boxwidth,points,log,remove_zero,start_at_one,font_size,xlabels,updated_default_dict,ref_line

       
       # updated_default_dict=set_values_from_url(default_dict)
       updated_default_dict=default_dict
       
       plot_settings=st.sidebar.expander("Plot Settings")
       plot_settings.subheader('Plot Widgets')
       # plot_settings.button("Reset Defaults",on_click=reset_all_defaults)
       multi_options=[None]+cols
       color=plot_settings.selectbox(label='Color',options=multi_options,index=multi_options.index(updated_default_dict['color']))
       facet=plot_settings.selectbox(label='Facet',options=multi_options,index=multi_options.index(updated_default_dict['facet']))
       height=plot_settings.slider(label='Height',min_value=300,max_value=1200,value=int(updated_default_dict['height']),step=50)
       font_size=plot_settings.slider(label='Font Size',min_value=1,max_value=25,value=int(updated_default_dict['font_size']))
       temp_opts=['SampleID/PlateID', 'Experiment', 'Bacteria', 'SampleOrigin',
       'TestedPhase', 'TimePoint', 'TestedAgent', 'TestedAgentDilution',
        'Plate']
       agg_opts=[]
       for opt in temp_opts:
              if opt in cols:
                     if len(df[opt].drop_duplicates())>1:
                            agg_opts.append(opt)
       if len(agg_opts)==0:
              agg_opts=['Average_by']
              

       
       names=plot_settings.multiselect(label='Name Samples By Chosen Columns',options=cols,default=agg_opts)
       boxwidth=plot_settings.slider(label='Box Width',min_value=0.1,max_value=1.0,value=float(updated_default_dict['boxwidth']),step=0.1)
       points=plot_settings.checkbox(label='Show Points', value=updated_default_dict['points'])
       xlabels=plot_settings.checkbox(label='Show X axis labels', value=updated_default_dict['xlabels'])
       log=plot_settings.checkbox(label='Log Y Axis', value=updated_default_dict['log'])
       start_at_one=plot_settings.checkbox(label='Start Axis at 1', value=updated_default_dict['start_at_one'],)#disabled=True)
       remove_zero=plot_settings.checkbox(label='Remove Zero Values', value=updated_default_dict['remove_zero'])
       ref_line=plot_settings.checkbox(label='Draw Reference Line', value=updated_default_dict['ref_line'])
       
def set_values_from_url(defdict):
       for val in defdict.keys():
              if val in st.experimental_get_query_params().keys():
                     defdict[val]=st.experimental_get_query_params()[val][0]
                     if defdict[val]=='None':
                            defdict[val]=None
                     elif defdict[val]=='True':
                            defdict[val]=True
                     elif defdict[val]=='False':
                            defdict[val]=False
       return defdict

# def reset_all_defaults():
#        updated_default_dict=default_dict
       
       
def add_custom_name_column():
       df_filtered['custom_name']=df_filtered[names].astype(str).agg('/'.join, axis=1)
       
       
def percent_survaviaviluty_section():
       st.markdown('---')
       st_survivability=st.container()
       st_survivability.subheader("% Survivability Plot")
       df=df_filtered
       choose_ref_sample=st_survivability.selectbox(label='Reference Sample',options=df_filtered['custom_name'].unique())
       choose_ref_type=st_survivability.selectbox(label='Min/Max/Mean/Median',options=['Mean','Median','Min','Max',])
       ref_opts=df[df['custom_name'].isin([choose_ref_sample])][y_variables]
       if choose_ref_type=='Min':
              ref_value=ref_opts.min().min()
       elif choose_ref_type=='Max':
              ref_value=ref_opts.max().max()
       elif choose_ref_type=='Median':
              ref_value=ref_opts.median().median()
       elif choose_ref_type=='Mean':
              ref_value=ref_opts.mean().mean()
       st_survivability.text(f"Reference value is set to the {choose_ref_type} value of '{choose_ref_sample}'. \n Chosen reference value is {ref_value}")
       y_norm=[val+'%' for val in y_variables]
       df[y_norm]=df[y_variables]*100/ref_value
       
       y_ref_excluded=[val+'_ref_excluded' for val in y_variables]
       df[y_ref_excluded]=df[y_variables]-ref_value
       # st_survivability.text(df)
       if color:
              df[color]=df[color].astype(str)
       fig=px.box(df,x='custom_name',y=y_norm,color=color,height=height,log_y=log,facet_col=facet,)
       fig.update_xaxes(showticklabels=xlabels)

       if log: 
              max_val=np.log10(df[y_norm].max().max())+0.5
              min_val=np.log10(df[y_norm].min().min())-0.5
              if start_at_one:
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     fig.update_layout(yaxis_range=[min_val,max_val])
                     
       else:
              max_val=df[y_norm].max().max()*1.05
              min_val=df[y_norm].min().min()*0.95
              if start_at_one:
                     fig.update_layout(yaxis_range=[0,max_val])
              else:
                     fig.update_layout(yaxis_range=[min_val,max_val])
                     
       fig.update_traces(width=boxwidth, boxmean=True)
       fig.update_xaxes(tickangle=90,matches=None,title=None,dtick=1)
       fig.update_yaxes(exponentformat='E')
       fig.update_layout(font=dict(size=font_size,))
       fig.update_layout(hovermode="x")
       if ref_line:
              fig.add_hline(y=100)
       if points:
            fig.update_traces(boxpoints='all')
       else:
            fig.update_traces(boxpoints=None)
       with st.spinner(text="In progress..."):
              st_survivability.plotly_chart(fig,use_container_width=True)
       # st_survivability
       
       st.markdown('---')
       st_survivability=st.container()
       st_survivability.subheader("Values minus reference Plot")
       st_survivability.text("Referece subtracted from the rest of the values.")
       st_survivability.text("Uses the reference sample chosen in the previous section.")
       fig2=px.box(df,x='custom_name',y=y_ref_excluded,color=color,height=height,facet_col=facet,)
       fig2.update_xaxes(showticklabels=xlabels)
       fig2.update_traces(width=boxwidth, boxmean=True)
       fig2.update_xaxes(tickangle=90,matches=None,title=None,dtick=1)
       fig2.update_yaxes(exponentformat='E')
       if ref_line:
              fig2.add_hline(y=0)
       if points:
            fig2.update_traces(boxpoints='all')
       else:
            fig2.update_traces(boxpoints=None)
       with st.spinner(text="In progress..."):
              st_survivability.plotly_chart(fig2,use_container_width=True)
       
       
       
       
       
def update_parameters_in_link():
              st.experimental_set_query_params(
                     color=color, 
                     facet=facet, 
                     height=height, 
                     names=names, 
                     boxwidth=boxwidth, 
                     points=points, 
                     log=log, 
                     remove_zero=remove_zero, 
                     start_at_one=start_at_one, 
                     font_size=font_size, 
                     xlabels=xlabels, 
                     **widget_dict
                     )
              

def main():
       # Main part of the app
       st_header_section()
       st_template_download()
       st_file_upload_section()
       if upload_data_widget:
              st_data_section()
              
              add_logo_and_links_to_sidebar()
              get_filters_and_add_widgets_to_sidebar(df)
              
              add_plot_settings_to_sidebar()
              # set_values_from_url()
              # update_parameters_in_link()
              filter_data()
              st_filtered_data_section()
              # add_custom_name_column()
              st_plot_section()
              # st_plot2_section()
              percent_survaviaviluty_section()
              
              
              
if __name__=='__main__':
       main()

# %%
