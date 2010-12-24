from google.appengine.ext import db


""" Used for aggregating data of various kinds.

For example:    Results of questionaries;
                Scores given to students;

There are lots of reports that system should be able to generate. Calculating various averages,
sums and medians on the fly could be quite resource intensive - so we decided to do this real-time
when new data is submitted to system.

Example:
new answer is submitted on feedback questionary form.
Tom (T) gave rating 4 to teacher Jim's (J) performance at "Modern Arts I" (MA) course.
Result is aggregated to 2**n-1 aggregations, where n is number of freedoms (important dimensions)* of answer.
Defining dimensions are always added to every combination.
Now rating is aggregated to combinations:
    T * FQ*F, J * FQ*F, MA * FQ*F, T*J * FQ*F, T*MA * FQ*F, J*MA * FQ*F, T*J*MA * FQ*F
and reports for these combinations are always up to date.

* dimension
dimension is measure of how many different participants are involved.
In example 1 there are 5 participants:
- T:  Student Tom                                       - important dimension;
- J:  Teacher Jim                                       - important dimension;
- MA: Subject "Modern Arts I"                           - important dimension;
- FQ: The feedback questionary                          - defining dimension;
- F:  Fact, that we are aggregating feedback results    - defining dimension.
"""
class Aggregation(db.Model):
    type            = db.StringProperty()
    level           = db.IntegerProperty()              # number of important dimensions
    dimensions      = db.StringListProperty()           # key@entity.property or key@entity
    count           = db.IntegerProperty()              # count of data units submitted to aggregation
    sum             = db.FloatProperty()                # sum of data units submitted to aggregation
    model_version   = db.StringProperty(default='A')

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