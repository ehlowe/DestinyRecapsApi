from core import utils
from core import services

from asgiref.sync import sync_to_async
from dataclasses import asdict

class StreamPlotController:
    @classmethod
    async def run(self, video_id):
        cost=0
        stream_recap_data=await utils.get_recap_data(video_id)

        annotated_results, major_topics, minor_topics, temp_cost = await services.stream_plot.generate_data(stream_recap_data)
        cost+=temp_cost

        plot_object, annotated_results, plot_segments, category_locations = await services.stream_plot.process_data(stream_recap_data,  annotated_results, major_topics, minor_topics, video_id)

        plot_object, temp_cost=await services.stream_plot.annotate_extra(video_id, stream_recap_data, plot_object)  
        cost+=temp_cost

        # save plot object to the database
        stream_recap_data.plot_object=asdict(plot_object)
        await sync_to_async(stream_recap_data.save)()

        # grab image and save it
        await services.stream_plot.visit_until_image_saved(video_id)

        print("Plotting Process Cost: ", cost)