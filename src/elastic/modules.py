from datetime import datetime, timedelta

class BaseImprovedSearch:
    # index = None
    # query_param = {"bool": {"must": []}}
    # filter_param = []
    sort_param = 'published_date:desc'
    per_param = 5
    search_fields = []

    def __init__(self, index, sort_param):
        self.index = index
        self.sort_param = sort_param
        self.query_param = {"bool": {"must": []}}
        self.filter_param = []

    async def search(self, search_val):
        if search_val:
            self.query_param['bool']['must'].append(
                {
                    "multi_match": {
                        "query": search_val,
                        "fields": self.search_fields,
                        "type": "phrase_prefix",
                        "operator": "or"
                    }
                }
            )
        # return self

    async def get(self, elastic_session, from_, per_page, author=None):
        self.query_param['bool']['must'].append(
            {"term": {"status.keyword": "P"}}
        )
        if self.filter_param:
            self.query_param['bool']['must'].append({"bool": {"must": self.filter_param}})
        if author:
            self.query_param['bool']['must'].append(
                {"term": {"author_ids.keyword": author}}
            )
        current_date = (datetime.now() + timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%SZ')
        date_filter = {
            "range": {
                "published_date": {
                    "lte": current_date
                }
            }
        }
        self.query_param['bool']['must'].append(date_filter)
        print(self.query_param)
        return await elastic_session.search(
            index=self.index,
            sort=self.sort_param,
            from_=(from_ - 1) * per_page,
            size=per_page,
            query=self.query_param
        )


class TagsImprovedSearch(BaseImprovedSearch):
    search_fields = ['title']
    index = 'tag'
    sort_param = 'title.keyword'


# class NewsImprovedSearch(BaseImprovedSearch):
#     search_fields = ['title', 'description', 'content']
#     index = 'news'
#     sort_param = ['title.keyword', 'description.keyword', 'content.keyword']


class ArticlesImprovedSearch(BaseImprovedSearch):
    search_fields = ['title', 'description', 'content']
    index = 'articles'
    # sort_param = ['title.keyword', 'description.keyword', 'content.keyword']

# class BlogsImprovedSearch(BaseImprovedSearch):
#     search_fields = ['title', 'description', 'content']
#     index = 'blogs'
#     sort_param = ['title.keyword', 'description.keyword', 'content.keyword']


class RatingImprovedSearch(BaseImprovedSearch):
    search_fields = ['name']
    index = 'rating'

    async def filter_by_authors(self, authors):
        if authors:
            self.filter_param.append({"terms": {"author_ids.keyword": authors}})

    async def filter_by_status(self, status_val):
        if status_val:
            self.filter_param.append({"term": {"status.keyword": status_val}})


class ObjectImprovedSearch(BaseImprovedSearch):
    search_fields = ['name']
    index = 'object'
    sort_param = 'name.keyword'

    async def filter_by_group(self, group_id):
        if group_id:
            self.filter_param.append({"term": {"group_id.keyword": str(group_id)}})


class AnouncImprovedSearch(BaseImprovedSearch):
    search_fields = ['number']
    index = 'anounc'


class FieldImprovedSearch(BaseImprovedSearch):
    # search_fields = ['title']
    index = 'field_rating'
    sort_param = 'order'

    async def filter_by_rating(self, rating_id):
        if rating_id:
            self.filter_param.append({"term": {"rating_id.keyword": str(rating_id)}})
