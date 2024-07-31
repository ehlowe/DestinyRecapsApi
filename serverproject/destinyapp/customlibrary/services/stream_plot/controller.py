from . import data_gen, data_processing, data_plotting, extra_annotations, get_image

from destinyapp.customlibrary import utils
from destinyapp.models import StreamRecapData


async def generate_data(stream_recap_data: StreamRecapData):
    cost=0
    text_chunks_no_overlap = await data_gen.create_text_chunks(stream_recap_data.transcript, 0)

    text_chunk_batches = await data_gen.generate_text_chunk_batches(text_chunks_no_overlap)

    topic_annotations_str, temp_cost = await data_gen.annotate_major_minor_topics(stream_recap_data.recap)
    cost+=temp_cost
    major_topics, minor_topics = data_gen.process_topic_annotations_str(topic_annotations_str)

    responses, annotated_results, temp_cost = await data_gen.annotate_all_batches(text_chunk_batches, topic_annotations_str)
    cost+=temp_cost

    return annotated_results, major_topics, minor_topics, cost

async def process_data(stream_recap_data: StreamRecapData, annotated_results, major_topics, minor_topics, video_id):
    annotated_segments, category_locations = await data_processing.create_segments(stream_recap_data.linked_transcript, annotated_results, major_topics, stream_recap_data.transcript)

    plot_segments=await data_processing.annotated_to_plot_segments(annotated_segments)

    plot_object=await data_processing.create_plot_object(plot_segments, category_locations, video_id)

    return plot_object, annotated_segments, plot_segments, category_locations

async def generate_plot(plot_object):
    return await data_plotting.generate_plot(plot_object)

async def annotate_extra(plot_object):
    cost=0
    plot_object, temp_cost=await extra_annotations.recap_segments(plot_object)
    cost+=temp_cost
    plot_object, temp_cost=await extra_annotations.recap_abstractions(plot_object)
    cost+=temp_cost
    return plot_object, cost

async def visit_until_image_saved(video_id):
    for i in range(3):
        await get_image.make_plot_save_request(video_id)

        stream_recap_data=await utils.get_recap_data(video_id)

        if len(stream_recap_data.plot_image)>100:
            break



# class StreamPlotController:
#     async def generate_data(stream_recap_data: StreamRecapData):
#         text_chunks_no_overlap = await data_gen.create_text_chunks(stream_recap_data.transcript, 0)

#         text_chunk_batches = await data_gen.generate_text_chunk_batches(text_chunks_no_overlap)

#         topic_annotations_str = await data_gen.annotate_major_minor_topics(stream_recap_data.recap)
#         major_topics, minor_topics = data_gen.process_topic_annotations_str(topic_annotations_str)

#         responses, annotated_results = await data_gen.annotate_all_batches(text_chunk_batches, topic_annotations_str)

#         return annotated_results, major_topics, minor_topics
    
#     async def process_data(stream_recap_data: StreamRecapData, annotated_results, major_topics, minor_topics, video_id):
#         annotated_segments, category_locations = await data_processing.create_segments(stream_recap_data.linked_transcript, annotated_results, major_topics, stream_recap_data.transcript)

#         plot_segments=await data_processing.annotated_to_plot_segments(annotated_segments)

#         plot_object=await data_processing.create_plot_object(plot_segments, category_locations, video_id)

#         return plot_object, annotated_segments, plot_segments, category_locations
    
#     async def generate_plot(plot_object):
#         return await data_plotting.generate_plot(plot_object)
    
# async def run(self, video_id):
#     stream_recap_data=await utils.get_recap_data(video_id)

#     annotated_results, major_topics, minor_topics = await StreamPlotController.generate_data(stream_recap_data)

#     plot_object, annotated_results, plot_segments, category_locations = await StreamPlotController.process_data(stream_recap_data,  annotated_results, major_topics, minor_topics, video_id)

#     await StreamPlotController.generate_plot(plot_object)