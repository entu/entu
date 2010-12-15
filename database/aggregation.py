from google.appengine.ext import db


class Aggregation(db.Model):
    type            = db.StringProperty()
    level           = db.IntegerProperty()
    dimensions      = db.StringListProperty()
    count           = db.IntegerProperty()
    sum             = db.FloatProperty()

    def add(self):

        for level in range(1, len(self.dimensions)+1):
            for t in list(combinations(self.dimensions, level)):
                dimensions = list(t)

                a = db.Query(Aggregation)
                a.filter('type', self.type)
                a.filter('level', level)
                for d in dimensions:
                    a.filter('dimensions', d)
                aggr = a.get()

                if aggr:
                    aggr.count = int(aggr.count) + 1
                    if self.sum:
                        if aggr.sum:
                            aggr.sum = aggr.sum + self.sum
                        else:
                            aggr.sum = self.sum

                else:
                    aggr = Aggregation()
                    aggr.type = self.type
                    aggr.level = level
                    aggr.dimensions = dimensions
                    aggr.count = 1
                    if self.sum:
                        aggr.sum = self.sum
                aggr.put()


def combinations(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)