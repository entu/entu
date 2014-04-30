var entuApp = angular.module('entuApp', ['ionic', 'ngResource']);
var entuAPI = '/api2/';

entuApp.config(function($stateProvider, $urlRouterProvider) {
    $stateProvider
        .state('eventmenu', {
            url: '',
            abstract: true,
            templateUrl: 'templates/menu.html'
        })
        .state('eventmenu.home', {
            url: '/home',
            views: {
                'menuContent' :{
                    templateUrl: 'templates/home.html'
                }
            }
        })
        .state('eventmenu.definition', {
            url: '/:definition',
            views: {
                'menuContent' :{
                    templateUrl: 'templates/list.html',
                    controller: 'listCtrl'
                }
            }
        })
        .state('eventmenu.entity', {
            url: '/:definition/:entity',
            views: {
                'menuContent' :{
                    templateUrl: 'templates/entity.html',
                    controller: 'entityCtrl'
                }
            }
        })
    $urlRouterProvider.otherwise('/home');
});

entuApp.controller('MainCtrl', function($scope, $resource, $ionicSideMenuDelegate) {
    $scope.entu_url = entuAPI;
    $scope.definitions = $resource(entuAPI+'definition').get();

    $scope.toggleLeft = function() {
        $ionicSideMenuDelegate.toggleLeft();
    };
});

entuApp.controller('listCtrl', function ($scope, $http, $stateParams, $timeout){
    $scope.entu_url = entuAPI;
    $scope.page = 0;

    $scope.loadEntities = function(reload) {
        if($scope.loading == true) return;
        $scope.loading = true;

        if(reload == true) $scope.page = 0;

        try {
            var loaded = $scope.entities.result.length;
            var total = $scope.entities.count;
        } catch(err) {
            var loaded = 0;
            var total = 1;
        }

        if(total > loaded) {
            $scope.page = $scope.page + 1;
            $http({method: 'GET', url: entuAPI+'entity', params: {definition: $stateParams.definition, limit:20, page:$scope.page}}).success(function(data) {
                if($scope.page > 1) {
                    $scope.entities.result = $scope.entities.result.concat(data.result);
                } else {
                    $scope.entities = data;
                }
                $scope.loading = false;
                $scope.$broadcast('scroll.infiniteScrollComplete');
                $scope.$broadcast('scroll.refreshComplete');
            });
        } else {
            $scope.noMoreItems = true;
            $scope.$broadcast('scroll.infiniteScrollComplete');
            $scope.$broadcast('scroll.refreshComplete');
        }
    };
    $scope.loadEntities();

    // var timer = false;
    // $scope.searchEntities = function () {
    //     if(timer) $timeout.cancel(timer);
    //     timer = $timeout(function () {
    //         $scope.entities = $resource(entuAPI, {action: 'entity', definition: $stateParams.definition, limit:20, query:$scope.query}).get();
    //     }, 1000)
    // };
});

entuApp.controller('entityCtrl', function ($scope, $http, $resource, $stateParams){
    $scope.loadEntity = function() {
        $http({method: 'GET', url: entuAPI+'entity-'+$stateParams.entity}).success(function(data) {
            $scope.entity = data;
            $scope.$broadcast('scroll.refreshComplete');
        });
        $scope.childs = $resource(entuAPI+'entity-'+$stateParams.entity+'/childs').get();
        $scope.referrers = $resource(entuAPI+'entity-'+$stateParams.entity+'/referrals').get();
    };
    $scope.loadEntity();
});
