/* 确定性随机数：实现 MT19937，提供与 Python random.Random 相近的接口。
   用于离线引擎的可复现随机（不必与 Python 逐位一致，但每次同种子结果相同）。 */
class Random {
  constructor(seed) {
    this.mt = new Uint32Array(624);
    this.idx = 624;
    let s = (seed >>> 0) || 1;
    this.mt[0] = s;
    for (let i = 1; i < 624; i++) {
      const x = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30);
      this.mt[i] = (Math.imul(1812433253, x) + i) >>> 0;
    }
  }
  _twist() {
    for (let i = 0; i < 624; i++) {
      const x = (this.mt[i] & 0x80000000) | (this.mt[(i + 1) % 624] & 0x7fffffff);
      let a = x >>> 1;
      if (x & 1) a ^= 0x9908b0df;
      this.mt[i] = (this.mt[(i + 397) % 624] ^ a) >>> 0;
    }
    this.idx = 0;
  }
  _u32() {
    if (this.idx >= 624) this._twist();
    let y = this.mt[this.idx++];
    y ^= y >>> 11;
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= y >>> 18;
    return y >>> 0;
  }
  random() { return this._u32() * (1.0 / 4294967296.0); }
  randint(a, b) { return a + Math.floor(this.random() * (b - a + 1)); }
  choice(arr) { return arr[Math.floor(this.random() * arr.length)]; }
}
