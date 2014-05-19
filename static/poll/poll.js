function getSignedData(user, key, data) {
    if(!user || !key) return;

    var conditions = []
    for(k in data) {
        conditions.push({k: data[k]});
    };

    var expiration = new Date();
    expiration.setMinutes(expiration.getMinutes() + 10);

    data['user'] = user;
    data['policy'] = CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(JSON.stringify({expiration: expiration.toISOString(), conditions: conditions})));
    data['signature'] = CryptoJS.enc.Base64.stringify(CryptoJS.HmacSHA1(data['policy'], key));

    return data;
}




angular.module('entuApp', ['ionic', 'angular.markdown'])
    .config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
            // $urlRouterProvider.otherwise('/');
            $stateProvider
            .state('poll', {
                url: '/:poll_id/:user_id/:key',
                controller: 'pollCtrl',
                templateUrl: 'poll.html',
            })
            .state('poll_check', {
                url: '/:poll_id/:user_id/:key/:check',
                controller: 'pollCtrl',
                templateUrl: 'poll.html',
            });
        }])
    .controller('pollCtrl', ['$scope', '$http', '$stateParams', '$ionicLoading', function($scope, $http, $stateParams, $ionicLoading) {
        if(!$stateParams.user_id || !$stateParams.key) return;

        $scope.is_loading = 1;
        $scope.request_count = 0;
        $scope.assessees = [];
        $scope.assessee_titles = {};
        $scope.questions = [];

        // Get questionary
        $http({
                method : 'GET',
                url    : '/api2/entity-' + $stateParams.poll_id,
                params : getSignedData($stateParams.user_id, $stateParams.key, {})
            })
            .success(function(data) {
                $scope.request_count += 1;
                try        { $scope.title = data.result.displayname; }
                catch(err) { $scope.title = ''; }
                try        { $scope.description = data.result.properties.pollheader.values[0].value; }
                catch(err) { $scope.description = ''; }
                try        { $scope.howto = data.result.properties.pollhowto.values[0].value; }
                catch(err) { $scope.howto = ''; }
            });

        // Get person
        $http({
                method : 'GET',
                url    : '/api2/entity-' + $stateParams.user_id,
                params : getSignedData($stateParams.user_id, $stateParams.key, {})
            })
            .success(function(data) {
                $scope.request_count += 1;
                try        { $scope.person = data.result.displayname; }
                catch(err) { $scope.person = ''; }
            });

        // Get user answers
        $http({
                method : 'GET',
                url    : '/api2/entity',
                params : getSignedData($stateParams.user_id, $stateParams.key, {definition: 'answer'})
            })
            .success(function(data) {
                $scope.request_count += 1;
                for (var a_idx in data.result) {
                    //Get test
                    $scope.is_loading += 1;
                    $http({
                            method : 'GET',
                            url    : '/api2/entity-' + data.result[a_idx].id,
                            params : getSignedData($stateParams.user_id, $stateParams.key, {})
                        })
                        .success(function(data) {
                            $scope.request_count += 1;
                            try        { var assessor_id = data.result.properties.assessor.values[0].db_value; }
                            catch(err) { var assessor_id = 0; }
                            try        { var assessee_id = data.result.properties.assessee.values[0].db_value; }
                            catch(err) { var assessee_id = 0; }
                            try        { var assessee = data.result.properties.assessee.values[0].value; }
                            catch(err) { var assessee = 0; }
                            try        { var title = data.result.properties.title.values[0].value; }
                            catch(err) { var title = ''; }
                            try        { var selftitle = data.result.properties.selftitle.values[0].value; }
                            catch(err) { var selftitle = ''; }
                            try        { var text = data.result.properties.text.values[0].id; }
                            catch(err) { var text = false; }
                            try        { var text_value = data.result.properties.text.values[data.result.properties.text.values.length-1].db_value; }
                            catch(err) { var text_value = ''; }
                            try        { var rating = data.result.properties.rating.values[0].id; }
                            catch(err) { var rating = false; }
                            try        { var rating_value = data.result.properties.rating.values[data.result.properties.rating.values.length-1].db_value; }
                            catch(err) { var rating_value = false; }
                            try        { var ordinal = data.result.properties.ordinal.values[0].value; }
                            catch(err) { var ordinal = 0; }

                            if(assessor_id == $stateParams.user_id) {
                                if(assessee_id == $stateParams.user_id) assessee = 'Hindan ennast';

                                if(!$scope.assessee_titles[assessee_id]) {
                                    $scope.assessee_titles[assessee_id] = assessee;
                                    $scope.assessees.push({
                                        id      : assessee_id,
                                        title   : assessee,
                                        ordinal : (assessee_id == $stateParams.user_id) ? 0 : 1
                                    });
                                }

                                if(!text_value) text_value = '';

                                $scope.questions.push({
                                    id           : data.result.id,
                                    assessee_id  : assessee_id,
                                    title        : (assessee_id == $stateParams.user_id) ? selftitle : title,
                                    text         : text,
                                    text_value   : (text_value.replace('.', '').replace(' ', '') == '') ? '' : text_value,
                                    rating       : rating,
                                    rating_value : (rating_value == -1) ? 50 : rating_value,
                                    no_rating    : (rating_value == -1) ? true : false,
                                    ordinal      : ordinal
                                });

                            }
                            $scope.is_loading -= 1;
                        });
                }
                $scope.is_loading -= 1;
            });

        $scope.showQuestions = function(id) {
            $scope.current_assessee = id;
        }

        $scope.loadingProgress = function() {
            var s = '';
            for (var i=0; i<$scope.is_loading/5; i++) s += '.';
            return s;
        }

        $scope.saveNoRating = function(row) {
            row.no_rating = true;
            row.rating_value = 50;
            $http({
                method : 'PUT',
                url    : '/api2/entity-' + row.id,
                data   : getSignedData($stateParams.user_id, $stateParams.key, {'answer-rating': -1})
            });
        }

        $scope.saveRating = function(row) {
            row.no_rating = false;
            $http({
                method : 'PUT',
                url    : '/api2/entity-' + row.id,
                data   : getSignedData($stateParams.user_id, $stateParams.key, {'answer-rating': row.rating_value})
            });
        }

        $scope.saveText = function(row) {
            $http({
                method : 'PUT',
                url    : '/api2/entity-' + row.id,
                data   : getSignedData($stateParams.user_id, $stateParams.key, {'answer-text': (row.text_value) ? row.text_value : '.'})
            });
        }

    }]);
