from haystack import indexes
from .models import Thread, Post


class ThreadIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='user')
    pub_date = indexes.DateTimeField(model_attr='pub_date')
    subforum = indexes.CharField(model_attr='subforum__title')
    rating = indexes.IntegerField()

    def prepare_rating(self, obj):
        return obj.get_rating()

    def get_model(self):
        return Thread

    # def prepare_subforum(self, obj):
    #     return obj.subforum.title



class PostIndex(ThreadIndex):
    subforum = indexes.CharField(model_attr='thread__subforum__title')

    def get_model(self):
        return Post

    # def prepare_subforum(self, obj):
    #     return obj.subforum.title

