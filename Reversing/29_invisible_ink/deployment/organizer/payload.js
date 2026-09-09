// oe-format internal seal -- build artifact, do not edit
const D=Buffer.from("UVdWS0NtX0FLQkZVQ0YARh1HXgVRHWtdREJeWFduUUYAH19tFlIdUABNSQ==","base64");const V="2.4.1";
function unseal(){let o="";for(let i=0;i<D.length;i++)o+=String.fromCharCode(D[i]^V.charCodeAt(i%V.length));return o;}
module.exports.unseal=unseal;
