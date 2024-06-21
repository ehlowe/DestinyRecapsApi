from django.urls import path
from . import views
urlpatterns = [
    path('auto', views.auto_recaps_generator, name='run_automated_annotater'),

    path('metas/', views.get_all_metas),
    path('details/', views.get_meta_details, name='get_meta_details'),

    path('get_query_index',views.get_scroll_index, name='get_scroll_index'),

    path('delete_transcripts', views.delete_transcripts, name='delete_transcripts'),

    path("view_raw_transcripts", views.view_raw_transcripts, name="view_raw_transcripts"),
]