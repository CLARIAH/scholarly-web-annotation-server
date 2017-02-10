// api-test.js
'use strict';

var expect = require('chai').expect;
require('es6-promise').polyfill();
require('isomorphic-fetch');
import AnnotationAPI from '../src/api/AnnotationAPI.js';
var uuid = require('uuid4');

let annotationInvalid = {
    "@context": "http://www.w3.org/ns/anno.jsonld",
    type: "Annotation",
    body: [
        {
            vocabulary: "DBpedia",
            purpose: "classifying",
            type: "Classifying",
            id: "http://dbpedia.org/resource/Vincent_van_Gogh",
            value: "Vincent van Gogh"
        }
    ],
    creator: "marijn"
};

let annotationValid = {
    "@context": "http://www.w3.org/ns/anno.jsonld",
    type: "Annotation",
    body: [
        {
            vocabulary: "DBpedia",
            purpose: "classifying",
            type: "Classifying",
            id: "http://dbpedia.org/resource/Vincent_van_Gogh",
            value: "Vincent van Gogh"
        }
    ],
    creator: "marijn",
    target: [
        {
            source: "urn:vangogh:testletter.sender",
            selector: null,
            type: "Text"
        }
    ]
};

describe('AnnotationAPI', function() {
    it('should exist', function() {
        expect(AnnotationAPI).to.not.be.undefined;
    });

});

describe('AnnotationAPI sending a non-existing resource ID', function() {
    it('should return an empty list', function(done) {
        let fakeId = "this-resource-does-not-exist";
        let expectedData = [];
        AnnotationAPI.getAnnotationsByTarget(fakeId, function(error, actualData) {
            expect(error).to.equal(null);
            expect(actualData).to.eql(expectedData);
            done();
        });
    });
});

describe('AnnotationAPI sending an object as resource ID', function() {

    it('should return an error', function(done) {
        let objectAsId = {"id": "this-resource-does-not-exist"};
        let expectedData = null;
        AnnotationAPI.getAnnotationsByTarget(objectAsId, function(error, actualData) {
            expect(error.name).to.equal("TypeError");
            expect(error.message).to.equal("resource ID should be string");
            expect(actualData).to.eql(expectedData);
            done();
        });
    });
});

describe('AnnotationAPI POSTing an annotation without a target', function() {

    it('should return an error', function(done) {
        AnnotationAPI.saveAnnotation(annotationInvalid, function(error, data) {
            expect(error.status).to.equal(400);
            expect(error.message).to.equal("annotation MUST have at least one target");
            done();
        });
    });
});


describe('AnnotationAPI handling a valid annotation', function() {

    var savedAnnotation;

    it('should return annotation with ID after POST', function(done) {
        AnnotationAPI.saveAnnotation(annotationValid, function(error, annotation) {
            expect(error).to.equal(null);
            expect(annotation.id).to.not.be.undefined;
            savedAnnotation = annotation;
            //expect(uuid.valid(id)).to.be.true;
            done();
        });
    });

    it('should return annotation after GET', function() {
        AnnotationAPI.getAnnotationById(savedAnnotation.id, function(error, annotation) {
            expect(error).to.equal(null);
            expect(annotation.id).to.equal(savedAnnotation.id);
            done();
        });
    });

    it('should return updated annotation after PUT', function() {
        let newTarget = "urn:vangogh:testletter.receiver";
        savedAnnotation.target.source = newTarget;
        AnnotationAPI.saveAnnotation(savedAnnotation, function(error, annotation) {
            expect(error).to.equal(null);
            expect(annotation.id).to.equal(savedAnnotation.id);
            expect(annotation.target.source).to.equal(newTarget);
        });
    });

    it('should return annotation after DELETE', function() {
        AnnotationAPI.deleteAnnotation(savedAnnotation, function(error, annotation) {
            expect(error).to.equal(null);
            expect(annotation.id).to.equal(savedAnnotation.id);
        });
    });

    it('should return an error after GETting deleted annotation', function(done) {
        AnnotationAPI.getAnnotationById(savedAnnotation.id, function(error, data) {
            expect(error.status).to.equal(404);
            expect(error.message).to.equal("There is no annotation with ID " + savedAnnotation.id);
            done();
        });
    });
});




