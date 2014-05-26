var entuApp = angular.module('entuApp', ['ngRoute', 'ngResource', 'ui.bootstrap']);
entuApp.config(['$routeProvider', function($routeProvider) {
    $routeProvider
        .when('/', {
            controller: 'menuCtrl'
        })
        .when('/:definition', {
            controller: 'listCtrl'
        })
        .when('/:definition/:entity', {
            controller: 'entityCtrl'
        })
        .otherwise({
            redirectTo: '/'
        });
}]);

entuApp.controller('mainCtrl', function ($scope, $http, $routeParams){
    $scope.pin_menu = true;
    $scope.pin_menu_label = 'unpin';
    $scope.hide_menu = false;

    $scope.page_title = 'Entu';

    $scope.pinMenu = function() {
        $scope.pin_menu = !$scope.pin_menu;
        $scope.pin_menu_label = ($scope.pin_menu) ? 'unpin' : 'pin';
    };

    $scope.showMenu = function() {
        if(!$scope.pin_menu) $scope.hide_menu = false;
    };

    $scope.hideMenu = function() {
        if(!$scope.pin_menu) $scope.hide_menu = true;
    };

    $scope.menuStyle = function(div) {
        if($scope.hide_menu) {
            if(div == 'sidebar') return {'left': '-168px'};
            if(div == 'list')    return {'left': '32px'};
            if(div == 'content') return {'left': '392px'};
            if(div == 'navbar')  return {'left': '-168px'};
        }
    };

});

entuApp.controller('menuCtrl', function($scope, $resource) {
    $scope.definitions = $resource('/api2/definition').get();
    for(x in $scope.definitions.result) {
        $scope.definitions.result[x].visible = false;
    }

    $scope.toggleMenuGroup = function(idx) {
        $scope.definitions.result[idx].visible = !$scope.definitions.result[idx].visible;
    };

});

entuApp.controller('listCtrl', function ($scope, $http, $routeParams){
    $http({method: 'GET', url: '/api2/entity', params: {definition: $routeParams.definition, limit:200}}).success(function(data) {
        $scope.entities = data;
    });
});

entuApp.controller('entityCtrl', function ($scope, $http, $resource, $routeParams){
    $scope.loadEntity = function() {
        $http({method: 'GET', url: '/api2/entity-'+$routeParams.entity}).success(function(data) {
            $scope.entity = data;
            $scope.$broadcast('scroll.refreshComplete');
        });
        $scope.childs = $resource('/api2/entity-'+$routeParams.entity+'/childs').get();
        $scope.referrers = $resource('/api2/entity-'+$routeParams.entity+'/referrals').get();
    };
    $scope.loadEntity();
});
