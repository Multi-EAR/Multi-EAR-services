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
  this.canvas.addEventListener("click", this.pause.bind(this));
  this.canvas.addEventListener("dblclick", this.reset.bind(this));
  this.context = this.canvas.getContext("2d");

  // Settings
  this.canvas.width = size;
  this.canvas.height = 80;
  this.width = 2;
  this.color = "#2f7ed8";
  this.enableGridLines = true;

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

  this.context.strokeStyle = this.color;
  this.context.lineWidth = this.width;

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
   * @RingBuffer.getFirstHeightPixel(height, value) - Returns the height of the first value in pixels based min/max
   * @RingBuffer.getHeightPixel(height, value) - Return the height of any value in pixels based on and min/max
   * @RingBuffer.plot(height, context) - Plots the ringbuffer to the passed canvas height & context
   *
   */

  this.size = size;
  this.index = 0;
  this.data = new Array(this.size).fill(0);
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

  // Keep track of the minimum and maximum values in the array
  this.scale = Math.max.apply(null, this.data.map(Math.abs));

}

RingBuffer.prototype.plot = function(height, context) {

  /*
   * Function RingBuffer.plot
   * Plots the ringbuffer to the passed context
   */

  // Begin of the curve
  context.moveTo(0, this.__getFirstHeightPixel(height));

  let index = 0;

  // Go over the ringbuffer in the correct order
  for(let i = this.index; i < this.data.length; i++) {
    context.lineTo(index++, 40 - this.__getHeightPixel(height, this.data[i]));
  }

  for(let i = 0; i < this.index; i++) {
    context.lineTo(index++, 40 - this.__getHeightPixel(height, this.data[i]));
  }

}

RingBuffer.prototype.__getFirstHeightPixel = function(height) {

  /*
   * Function RingBuffer.getFirstHeightPixel
   * Returns the pixel height of the first sample in the ringbuffer
   */

  return 40 - this.__getHeightPixel(height, this.data[this.index]);

}

RingBuffer.prototype.__getHeightPixel = function(height, value) {

  /*
   * Function RingBuffer.__getHeightPixel
   * Returns the pixel height of the first sample in the ringbuffer
   */

  return 0.5 * Math.round(height * value / this.scale);

}