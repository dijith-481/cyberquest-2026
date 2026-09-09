// oe-format 2.4.1 — string helpers for the badge-printing pipeline.  	 				  	 
// Vendored from the parallel-universe npm mirror. Dependency-free.				  	      		 				 		  
// lint: prettier --check passes — no trailing whitespace.	 	  	 		 	 		  		  		 			
//	 			  	  	
// v1 receipt cyber_quest{d3pr3c4t3d_v1_s3al_r3m0v3d} retired with 2.0 — do not use.	 		 	 		
'use strict';    	 			 	    	     
 		 	  	 		 			  			 	  
function pad2(n) { 		  	 	
  const s = String(n); 			  	  		 			  		    
  return s.length >= 2 ? s : '0' + s;	 		 		    	      	
}		  		 		  	
 	 		    	 		 	
function padEnd(s, w, ch) {	    	       	 		 	  
  s = String(s);	 		 	  	      		   	  			 	 	 		 	  	 		
  ch = ch === undefined ? ' ' : String(ch); 		   		  	    	      
  while (s.length < w) s = s + ch;		    	 			  	  
  return s.slice(0, w);			 	   		 
}	  	 		  		  		   
 	 		   		 	
function padStart(s, w, ch) {		 	    	 		
  s = String(s);    	      		  	 
  ch = ch === undefined ? ' ' : String(ch);  		 				  	      		 			  		 				 
  while (s.length < w) s = ch + s;			 	    	   
  return s.slice(-w);   		  	 	 		  
}	   		 	  	 			 	      	 	  
		   		 		 				 		 			  			  		 
function trimLines(text) {			 	    	      	   	    
  return String(text)				 	 	    	  			 	 	
    .split('\n') 		  		  		  		  		  	 	 			
    .map(function (l) { return l.trim(); })  	   	 			  		  		  			  	  		
    .join('\n'); 				 		 		 	  	
} 	     	   	  	 	 	 	 	 	 	
	  		  	   	 	 		
function slugify(text) {	 	 	  		  		     	  			  	
  return String(text)		 	   	 		     		   
    .toLowerCase()  	   		  	  		   	 	   	 		 	 		 	 	
    .replace(/[^a-z0-9]+/g, '-')	 	  	 	
    .replace(/^-+|-+$/g, '') 		  	 	   	  		     	 		  	 	     
    .slice(0, 64);	 	 	  	  		 	   
}  		   	 	  	    	 
		    		  			 
function truncate(text, n) {	 	 		  	 	
  const s = String(text);  	  	  	    	 	 
  if (s.length <= n) return s;			 			 	   		  	   	 	
  return s.slice(0, n - 1) + '…';  	  	   	 	 	  	 	  		  
}	 	 	 	 			 	   		  		  	   			 	 	
 	 	 	 	 	 	 	 	 	 		  	 	    
function initials(name) { 	 	  	     		   	  
  return String(name)			  	 			 	   	 
    .split(/\s+/)  		  		 		   	  	 
    .filter(Boolean) 	 		  	   	 	 	 	 	    
    .map(function (w) { return w[0].toUpperCase(); }) 	 	    	  	  			  	 	  		 	 	   	  				 	  				 
    .join('');	  	   	   	 		   
} 	   	  		   	  		  
  	 			  
function maskEmail(addr) {		 		  	 	  		 	
  const parts = String(addr).split('@');	   		 	    	   	
  if (parts.length !== 2) return '***';   	 	  	  			 		 		   
  const user = parts[0];		 		 				 		
  const keep = user.slice(0, 2); 			  			  		 	
  return keep + '***@' + parts[1];		 	    	 
}     	 	 		 
  				 	  	   	   		  	  
function capitalize(word) { 	 			   		 	    	 			 
  const s = String(word);  		   	  	   	   	
  if (!s) return s;		 		    	 	  		  
  return s[0].toUpperCase() + s.slice(1).toLowerCase();		  			 	 	 		 			  		   	
}	 			 	   		 	  	
 		 				 		
function titleCase(text) { 			   	      			 	 	 		
  return String(text).split(' ').map(capitalize).join(' '); 			  			  		 		  	 	 		
}    	 		 		    	 	   
  	 	  	 				 		 	
function countOcc(haystack, needle) {	 		   		  	 	 			 	    	
  if (!needle) return 0;      		 				  	
  let n = 0;			 	  	   	   	   	   		
  let i = String(haystack).indexOf(needle);	 		 		  	
  while (i !== -1) {	  		 				 			  	   	 	    
    n += 1;		 		   		  	 	 			 	    	  
    i = String(haystack).indexOf(needle, i + needle.length);    		 	  	  				 	  		    
  }  			 		 		 	  	  				   	  
  return n; 	    	 			 
} 		 		   		  
	 	 		 			  		
function lines(text) {  			 			 	   		 
  return String(text).split('\n');	     			 		 		 	  	  	 	 		  	 	 
}		  	 	  	 		 				 
 	 	 		 
function unlines(arr) { 				 	 	 	  		 			 	   			 
  return arr.join('\n'); 	  		 	  	 		 			  		 
} 			  	 			  		  		
  			  	  		 				 		 		 	 	    		 		 	    		  
function stamp(d) {  	 			  	  	    		 		 				 		  	   		
  const t = d instanceof Date ? d : new Date(d);  	 	  	 	    	   	   	 		 
  return t.getFullYear() + '-' + pad2(t.getMonth() + 1) + '-' + pad2(t.getDate());		 		 	  	 	 			 	 	 				  	 	 		   	 	
}		  		   		 		 	    		  
  	 			  	  	    		 		 	
module.exports = {			 		  	   		  	 	 	     	 			 	   
  pad2: pad2, 	 	    		 	  	  	  	 	 	 	 		   	 			  		 	
  padEnd: padEnd,	   		  	 	 		 			  	
  padStart: padStart,	  			 			 	   		 	     	 
  trimLines: trimLines,	  	  	 	  	  			 		 			  
  slugify: slugify,	  		  	 	 			 	   			 	 	 			  	  	
  truncate: truncate,	 			   	      		 				  			 		 					 	    	 	  		
  initials: initials, 		 	 		 				 		  	   
  maskEmail: maskEmail,			 	 	 		 		   		  	 	  	 			  		 
  capitalize: capitalize, 	 	 				  
  titleCase: titleCase,  			     		 				 			 
  countOcc: countOcc, 	  			 	   			  		  	 
  lines: lines,			  			 	 	 		 			  			  		 		  	 	 	
  unlines: unlines,	    	 		 		    				 	 		
  stamp: stamp,	 	 	 		 			  			  		 		  	 	 		    	 		 
};		    			 		    	 	 
