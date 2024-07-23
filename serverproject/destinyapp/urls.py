from django.urls import path
from . import views

# from . import views_v2_async
urlpatterns = [

    # Page Loading Views
    path('recaps/', views.get_all_recaps),
    path('recap_details', views.get_recap_details, name='get_recap_details'),
    path('linked_transcript', views.get_linked_transcript, name='get_linked_transcript'),
    path('slow_recap_details', views.get_slow_recap_details, name='get_slow_recap_details'),


    path('generate_recap', views.auto_recaps_request, name='generate_recap'),
    path('update', views.recap_update_request, name='recap_update_request'),

    # Search View
    path('get_query_index',views.search, name='get_scroll_index'),


    path('dl', views.download_stream_recap_data, name='download_stream_recap_data'),

    # download stream data
    path('dl', views.download_stream_recap_data, name='download_stream_data'),




    path('delete_stream_recap_data', views.delete_stream_recap_data, name='delete_stream_recap_data'),



    

    # path('recaps/', views_v2_fresh.get_all_metas),
    # path('auto', views.auto_recaps_request, name='run_automated_annotater'),

    # path('metas/', views.get_all_metas),
    # path('details/', views.get_meta_details, name='get_meta_details'),
    # path("linked_transcript", views.get_meta_linked_transcript, name="get_linked_transcript"),

    # path('get_query_index',views.get_scroll_index, name='get_scroll_index'),

    # path('delete_transcripts', views.delete_transcripts, name='delete_transcripts'),

    # path("view_raw_transcripts", views.view_raw_transcripts, name="view_raw_transcripts"),

    # path("redo", views.redo_recaps_request, name="redo_recaps_request"),
]