from django.urls import path
from . import views

urlpatterns = [
    # Page Loading Views
    path('recaps/', views.get_all_recaps),
    path('recap_details', views.get_recap_details, name='get_recap_details'),
    path('linked_transcript', views.get_linked_transcript, name='get_linked_transcript'),
    path('slow_recap_details', views.get_slow_recap_details, name='get_slow_recap_details'),

    # Search View
    path('get_query_index',views.search, name='get_scroll_index'),

    # Chat view
    path('chatbot_response', views.chatbot_response, name='chatbot_response'),
    path('homepage_chatbot_response', views.homepage_chatbot_response, name='homepage_chatbot_response'),

    # Recap Generation Views
    path('generate_recap', views.auto_recaps_request, name='generate_recap'),
    path('manual_generate_recap', views.manual_recaps_request, name='manual_generate_recap'),
    path('update', views.recap_update_request, name='recap_update_request'),

    # download stream data
    path('dl', views.download_stream_recap_data, name='download_stream_data'),

    # delete stream data
    path('delete_stream_recap_data', views.delete_stream_recap_data, name='delete_stream_recap_data'),

    # save png
    path('save_png', views.SaveImageView.as_view(), name='save_png'),

]