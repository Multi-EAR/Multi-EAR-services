const TimeseriesGraph = function(element, size) {

  /*
   * Class TimeseriesGraph
   * Container for a single timeseries graph that can be plot dynamically
   *
   * API:
   *
   * @TimeseriesGraph.reset - resets the timeseries graph by clearing all data
   * @TimeseriesGraph.pause - toggles paused/not paused for drawing timeseries graph
   * @TimeseriesGraph.add - Adds a new value to the timeseries graph
   *
   */

  this.canvas = element;
  this.name = element.getAttribute("name");
  this.canvas.addEventListener("click", this.pause.bind(this));
  this.canvas.addEventListener("dblclick", this.reset.bind(this));
  this.context = this.canvas.getContext("2d");
  this.first = false;

  // Settings
  this.canvas.width = size;
  this.canvas.height = 100;
  this.width = 2;
  this.color = "#2f7ed8";
  this.gradient = this.__createGradient();

  this.enableGridLines = true;
  this.enableGradient = false;

  // Ringbuffer that stores the data of size N
  this.ringbuffer = new RingBuffer(size);

}

TimeseriesGraph.prototype.reset = function() {

  /*
   * Function TimeseriesGraph.reset
   * Resets the timeseries graph by re-creating the ringbuffer
   */

  this.ringbuffer = new RingBuffer(this.ringbuffer.size);

}

TimeseriesGraph.prototype.pause = function() {

  /*
   * Function TimeseriesGraph.pause
   * Pauses or continues rendering of the timeseries graph
   */

  this.__paused = !this.__paused;

}

TimeseriesGraph.prototype.add = function(value) {

  /*
   * Function TimeseriesGraph.add
   * Adds a value to the timeseries graph
   */

  this.ringbuffer.add(value);

  if(this.__paused) {
    return;
  }

  this.__draw();

}

TimeseriesGraph.prototype.__drawGridLines = function() {

  /*
   * Function TimeseriesGraph.__drawGridLines
   * Draws grid lines to the canvas
   */

  let nGridLinesWidth = 20;
  let nGridLinesHeight = 8;

  this.context.strokeStyle = "lightgrey";
  this.context.lineWidth = 1;

  let nx = Math.round(this.canvas.width / nGridLinesWidth);

  // Ten lines
  for(let i = 0; i < nGridLinesWidth; i++) {
    this.context.beginPath();
    this.context.moveTo(0.5 + nx * i, 0);
    this.context.lineTo(0.5 + nx * i, this.canvas.height);
    this.context.stroke();
  }

 // Three lines
 let ny = Math.round(this.canvas.height / nGridLinesHeight);

  for(let i = 0; i < nGridLinesHeight; i++) {
    this.context.beginPath();
    this.context.moveTo(0, 0.5 + ny * i);
    this.context.lineTo(this.canvas.width, 0.5 + ny * i);
    this.context.stroke();
  }

}

TimeseriesGraph.prototype.__createGradient = function() {

  /*
   * Function TimeseriesGraph.__createGradient
   * Creates a 3-color gradient for the line
   */

  let gradient = this.context.createLinearGradient(0, 0, 0, this.canvas.height);

  gradient.addColorStop("0.1", "red");
  gradient.addColorStop("0.5" , "white");
  gradient.addColorStop("0.9", "blue");

  return gradient;

}

TimeseriesGraph.prototype.__draw = function() {

  /*
   * Function TimeseriesGraph.__draw
   * Redrws the time series graph to the screen
   */

  // Clear the full canvas
  this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

  if(this.enableGridLines) {
    this.__drawGridLines();
  }

  this.context.lineWidth = this.width;

  if(this.enableGradient) {
    this.context.strokeStyle = this.gradient;
  } else {
    this.context.strokeStyle = this.color;
  }

  // Draw curve
  this.context.beginPath();
  this.ringbuffer.plot(this.canvas.height, this.context);
  this.context.stroke();

}

const RingBuffer = function(size) {

  /*
   * Class RingBuffer
   * Ringbuffer of size N that keeps data and evicts FIFO
   *
   * API:
   *
   * @RingBuffer.add - Adds a value to the ringbuffer
   * @RingBuffer.getHeightPixel(height, value) - Return the height of any value in pixels based on and min/max
   * @RingBuffer.plot(height, context) - Plots the ringbuffer to the passed canvas height & context
   *
   */

  this.size = size;
  this.index = 0;
  this.data = new Array(this.size).fill(null);
  this.previousScale = 0;

}

RingBuffer.prototype.add = function(value) {

  /*
   * Function RingBuffer.add
   * Adds a value to the ringbuffer
   */

  // Set at the current index
  this.data[this.index] = value;
  this.index = (this.index + 1) % this.size;

  // The mean of the series
  this.mean = this.data.reduce((a, b) => a + b, 0) / this.data.filter(x => x !== null).length;

  // Keep track of the minimum and maximum values in the array
  this.scale = Math.max.apply(null, this.data.filter(x => x!== null).map(x => Math.abs(x - this.mean)));

}

RingBuffer.prototype.plot = function(height, context) {

  /*
   * Function RingBuffer.plot
   * Plots the ringbuffer to the passed context
   */

  let index = 0;

  this.first = true;

  // Go over the ringbuffer in the correct order
  for(let i = this.index; i < this.data.length; i++) {
    this.__drawSample(context, height, index++, i);
  }

  for(let i = 0; i < this.index; i++) {
    this.__drawSample(context, height, index++, i);
  }

}

RingBuffer.prototype.__drawSample = function(context, height, x, i) {

  /*
   * Function RingBuffer.__drawSample
   * Draws a single sample to the canvas by moving the line to the appropriate position
   */

  if(this.data[i] === null) {
    return;
  }

  if(this.first) {
    context.moveTo(x, 0.5 * height - this.__getHeightPixel(height, this.data[i]));
    this.first = false;
  } else {
    context.lineTo(x, 0.5 * height - this.__getHeightPixel(height, this.data[i]));
  }

}

RingBuffer.prototype.__getHeightPixel = function(height, value) {

  /*
   * Function RingBuffer.__getHeightPixel
   * Returns the pixel height of the first sample in the ringbuffer
   */

  return 0.5 * Math.round(height * (value - this.mean) / this.scale);

}
