var should = require('chai').should(),
  Swap_class = require('../build/swapper.js');


describe('Swapper.clean(obj)', function () {

  it('should clear the content of an object', () => {
    let obj = { a: 1 };
    Swap_class.clean(obj);
    obj.should.eql({});
  });

  it('should clear an arry', () => {
    let arr = [1, 2, 3];
    Swap_class.clean(arr);
    arr.should.eql([]);
    arr.length.should.equal(0);
  });

  it('should clear an array with properties', () => {
    let arr = [1, 2, 3];
    arr.test = 'test value';
    Swap_class.clean(arr);
    arr.should.eql([]);
    arr.length.should.equal(0);
  });

});

describe('Swapper.obj(a,b)', () => {

  it('should swap objects', () => {
    let a = { v: 1 },
      b = { v: 2 };
    Swap_class.obj(a, b);
    a.should.eql({ v: 2 });
    b.should.eql({ v: 1 });
  });

  it('should swap arrays - equal length', () => {
    let a = [1, 2, 3],
      b = [9, 8, 7];
    Swap_class.obj(a, b);
    a.should.eql([9, 8, 7]);
    b.should.eql([1, 2, 3]);
  });

  it('should swap arrays - first shorter', () => {
    let a = [1, 2, 3],
      b = [9, 8, 7, 6];
    Swap_class.obj(a, b);
    a.should.eql([9, 8, 7, 6]);
    b.should.eql([1, 2, 3]);
  });

  it('should swap arrays - first longer', () => {
    let a = [1, 2, 3, 4],
      b = [9, 8, 7];
    Swap_class.obj(a, b);
    a.should.eql([9, 8, 7]);
    b.should.eql([1, 2, 3, 4]);
  });

});

describe('Swapper.elem(obj,prop1,prop2)', () => {

  it('should swap properties', () => {
    let a = { one: 1, two: 2 };
    Swap_class.elem(a, 'one', 'two');
    a.one.should.equal(2);
    a.two.should.equal(1);
  });

  it('should swap properties given as single string (space separated)', () => {
    a = { one: 1, two: 2 };
    Swap_class.elem(a, 'one two');
    a.one.should.equal(2);
    a.two.should.equal(1);
  });

});

describe('Swapper.parseNames(names)', () => {

  it('should parse names from given string - space', () => {
    Swap_class.parseNames('one two three').should.eql(['one', 'two', 'three']);
  });

  it('should parse names from given string - coma', () => {
    Swap_class.parseNames('one,two,three').should.eql(['one', 'two', 'three']);
  });

  it('should parse names from given string - tab', () => {
    Swap_class.parseNames('one	two	three').should.eql(['one', 'two', 'three']);
  });

  it('should parse names from given string - tab', () => {
    Swap_class.parseNames('one;two;three').should.eql(['one', 'two', 'three']);
  });

  it('should parse names from given string - multiple spaces', () => {
    Swap_class.parseNames('one  two  three').should.eql(['one', 'two', 'three']);
  });

  it('should parse names from given string - mixed separator', () => {
    Swap_class.parseNames('one  two;three,four five	six').should.eql(['one', 'two', 'three','four','five','six']);
  });

});

