// api-test.js
'use strict';

var expect = require('chai').expect;
require('es6-promise').polyfill();
require('isomorphic-fetch');
import AnnotationAPI from '../src/api/AnnotationAPI.js';

describe('AnnotationAPI', function() {
    it('should exist', function() {
        expect(AnnotationAPI).to.not.be.undefined;
    });

});

describe('getAnnotationsByTarget sending a non-existing ID', function() {

    var err = null;
    var actual = null;
    let fakeId = "this-resource-does-not-exist";
    beforeEach(function(done) {
        AnnotationAPI.getAnnotationsByTarget(fakeId, function(error, data) {
            err = error;
            actual = data;
            done();
        });
    });

    it('should return an empty list', function() {
        let expected = [];
        expect(err).to.equal(null);
        expect(actual).to.eql(expected);
    });
});

describe('getAnnotationsByTarget sending an object as ID', function() {

    var err = null;
    var actual = null;
    let fakeId = {"id": "this-resource-does-not-exist"};
    beforeEach(function(done) {
        AnnotationAPI.getAnnotationsByTarget(fakeId, function(error, data) {
            err = error;
            actual = data;
            done();
        });
    })
    it('should return an error', function() {
        let expected = null;
        expect(err.name).to.equal("TypeError");
        expect(err.message).to.equal("resource ID should be string");
        expect(actual).to.eql(expected);
    })
});
