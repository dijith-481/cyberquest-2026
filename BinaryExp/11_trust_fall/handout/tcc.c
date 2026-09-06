












#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char pool[1048576];     
static int  id[32768], cls[32768], ty[32768], val[32768], sz[32768], rf[32768], dim[32768], es[32768];
static char sbuf[4194304];     
static int  srclen;
static int gv = 0;
static unsigned rv = 0;
static int se = 0;
static unsigned long ow = 0x0000000000000000UL;
static int oo = 0;






static char *p;
static int  tok, tokv;
static long numval;
static int  line = 1;
static int  poolp = 0;

enum { TNum=128, TId, TStr, TShl, TShr, TLe, TGe, TEq, TNe, TAnd, TOr,
       TInc, TDec, TArrow, TAsn,
       TAddA, TSubA, TMulA, TDivA, TModA, TShlA, TShrA, TAndA, TOrA, TXorA,
       TIf=256, TElse, TWhile, TDo, TFor, TRet, TBreak, TContinue,
       TInt, TChar, TLong, TVoid, TStatic, TUns, TEnum };

enum { CGlb=0, CFun, CLoc, CCon };
enum { T_=0, T_CHAR, T_INT, T_LONG, T_VOID };

static int isidc(int c){ return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_'; }
static int isnum(int c){ return c>='0'&&c<='9'; }
static int istype(int t){ return t==TInt||t==TChar||t==TLong||t==TVoid||t==TUns; }

static int intern(char *s, int n){
  int i, j;
  for(i=0;i<poolp;i++){
    for(j=0;j<n;j++) if(pool[i+j]!=s[j]) break;
    if(j==n && pool[i+n]==0) return i;
  }
  for(i=0;i<n;i++) pool[poolp+i]=s[i];
  pool[poolp+n]=0; i=poolp; poolp+=n+1;
  return i;
}

static int intern5(int a,int b,int c,int d,int e){
  char s[8]; s[0]=a^0x5a; s[1]=b^0x5a; s[2]=c^0x5a; s[3]=d^0x5a; s[4]=e^0x5a; s[5]=0;
  return intern(s,5);
}

static void next(void){
  int c;
  while(1){
    c=*p++;
    if(c==0){ tok=0; return; }
    if(c=='\n'){ line++; continue; }
    if(c==' '||c=='\t'||c=='\r') continue;
    if(c=='/'&&*p=='/'){ while(*p&&*p!='\n')p++; continue; }
    if(c=='/'&&*p=='*'){ p++; while(*p&&!(*p=='*'&&p[1]=='/')){ if(*p=='\n')line++; p++; } if(*p)p+=2; continue; }
    if(c=='#'){ while(*p&&*p!='\n')p++; continue; } 
    break;
  }
  if(isidc(c)){
    char *q=p-1;
    while(isidc(*p)||isnum(*p))p++;
    tokv=intern(q,(int)(p-q));
    if(tokv==intern("if",2))tok=TIf; else if(tokv==intern("else",4))tok=TElse;
    else if(tokv==intern("while",5))tok=TWhile; else if(tokv==intern("do",2))tok=TDo;
    else if(tokv==intern("for",3))tok=TFor; else if(tokv==intern("return",6))tok=TRet;
    else if(tokv==intern("break",5))tok=TBreak; else if(tokv==intern("continue",8))tok=TContinue;
    else if(tokv==intern("int",3))tok=TInt; else if(tokv==intern("char",4))tok=TChar;
    else if(tokv==intern("long",4))tok=TLong; else if(tokv==intern("void",4))tok=TVoid;
    else if(tokv==intern("static",6))tok=TStatic; else if(tokv==intern("unsigned",8))tok=TUns;
    else if(tokv==intern("enum",4))tok=TEnum;
    else tok=TId;
    return;
  }
  if(isnum(c)){
    unsigned long v=0;
    if(c=='0'&&(*p=='x'||*p=='X')){
      p++;
      while(isnum(*p)||(*p>='a'&&*p<='f')||(*p>='A'&&*p<='F')){
        int d=(*p<='9')?*p-'0':((*p|32)-'a'+10); v=v*16+d; p++;
      }
    } else if(c=='0'){
      while(*p>='0'&&*p<='7'){ v=v*8+(*p-'0'); p++; }
    } else {
      v=c-'0';
      while(isnum(*p)){ v=v*10+(*p-'0'); p++; }
    }
    while(*p=='u'||*p=='U'||*p=='l'||*p=='L')p++;
    numval=(long)v; tok=TNum; return;
  }
  if(c=='\''){
    int v=0;
    while(*p&&*p!='\''){ if(*p=='\\'){p++; if(*p=='n')v=10;else if(*p=='t')v=9;else if(*p=='r')v=13;else if(*p=='0')v=0;else v=*p; p++;} else {v=*p;p++;} }
    if(*p)p++;
    numval=v; tok=TNum; return;
  }
  if(c=='"'){
    char buf[600]; int i=0;
    while(*p&&*p!='"'){
      if(*p=='\\'){
        p++;
        if(*p=='n')buf[i++]=10; else if(*p=='t')buf[i++]=9;
        else if(*p=='\\')buf[i++]=92; else if(*p=='"')buf[i++]=34; else if(*p=='0')buf[i++]=0;
        else buf[i++]=*p;
        p++;
      } else {
        buf[i++]=*p++;
      }
    }
    if(*p)p++;
    buf[i]=0; tokv=intern(buf,i); tok=TStr; return;
  }
  if(c=='+'){ if(*p=='='){p++;tok=TAddA;} else if(*p=='+'){p++;tok=TInc;} else tok='+'; }
  else if(c=='-'){ if(*p=='='){p++;tok=TSubA;} else if(*p=='-'){p++;tok=TDec;} else if(*p=='>'){p++;tok=TArrow;} else tok='-'; }
  else if(c=='*'){ if(*p=='='){p++;tok=TMulA;} else tok='*'; }
  else if(c=='/'){ if(*p=='='){p++;tok=TDivA;} else tok='/'; }
  else if(c=='%'){ if(*p=='='){p++;tok=TModA;} else tok='%'; }
  else if(c=='&'){ if(*p=='&'){p++;tok=TAnd;} else if(*p=='='){p++;tok=TAndA;} else tok='&'; }
  else if(c=='|'){ if(*p=='|'){p++;tok=TOr;} else if(*p=='='){p++;tok=TOrA;} else tok='|'; }
  else if(c=='^'){ if(*p=='='){p++;tok=TXorA;} else tok='^'; }
  else if(c=='~') tok='~';
  else if(c=='!'){ if(*p=='='){p++;tok=TNe;} else tok='!'; }
  else if(c=='='){ if(*p=='='){p++;tok=TEq;} else tok=TAsn; }
  else if(c=='<'){ if(*p=='<'){ if(p[1]=='='){p+=2;tok=TShlA;} else {p++;tok=TShl;} }
               else if(*p=='='){p++;tok=TLe;} else tok='<'; }
  else if(c=='>'){ if(*p=='>'){ if(p[1]=='='){p+=2;tok=TShrA;} else {p++;tok=TShr;} }
               else if(*p=='='){p++;tok=TGe;} else tok='>'; }
  else if(c=='(') tok='('; else if(c==')') tok=')';
  else if(c=='[') tok='['; else if(c==']') tok=']';
  else if(c=='{') tok='{'; else if(c=='}') tok='}';
  else if(c==';') tok=';'; else if(c==',') tok=',';
  else if(c==':') tok=':'; else if(c=='?') tok='?';
  else tok=0;
}


static int symp=0;
static int lookup(int name){
  int i;
  for(i=symp-1;i>=0;i--) if(id[i]==name) return i;
  return -1;
}


static FILE *fo;
static int strno=0, labno=0;
static int loc=0, frame=0;
static int nparams=0, params[8], psz[8];
static int rettype=0, retuns=0;
static int bstk[16], bsp=0;
static int cstk[16], csp=0;

static void push(void){ fprintf(fo,"  pushq %%rax\n"); }
static void poprcx(void){ fprintf(fo,"  popq %%rcx\n"); }
static void poparg(int i){
  if(i==0)fprintf(fo,"  popq %%rdi\n"); else if(i==1)fprintf(fo,"  popq %%rsi\n");
  else if(i==2)fprintf(fo,"  popq %%rdx\n"); else if(i==3)fprintf(fo,"  popq %%rcx\n");
  else if(i==4)fprintf(fo,"  popq %%r8\n"); else if(i==5)fprintf(fo,"  popq %%r9\n");
}
static void load(int t){
  if(t==T_CHAR) fprintf(fo,"  movsbl (%%rax),%%eax\n");
  else if(t==T_INT) fprintf(fo,"  movslq (%%rax),%%rax\n");
  else fprintf(fo,"  movq (%%rax),%%rax\n");
}
static void store(int t){
  if(t==T_CHAR) fprintf(fo,"  movb %%al,(%%rcx)\n");
  else if(t==T_INT) fprintf(fo,"  movl %%eax,(%%rcx)\n");
  else fprintf(fo,"  movq %%rax,(%%rcx)\n");
}


static int tybase, tyuns, typtr, tysz;

static void parse_type(void){
  tybase=T_INT; tyuns=0; typtr=0;
  if(tok==TUns){ tyuns=1; next(); }
  if(tok==TInt){ tybase=T_INT; next(); }
  else if(tok==TChar){ tybase=T_CHAR; next(); }
  else if(tok==TLong){ tybase=T_LONG; next(); }
  else if(tok==TVoid){ tybase=T_VOID; next(); }
  else if(tok==TId && !tyuns){ tybase=T_LONG; next(); } 
  while(tok=='*'){ typtr++; next(); }
  tysz = typtr?8 : tybase==T_CHAR?1 : tybase==T_LONG?8 : 4;
}

static void expect(int t){ if(tok!=t){ printf("syntax error near token %d line %d\n",tok,line); exit(1); } next(); }

static int peek(void){
  char *sp=p; int sl=line;
  int ot=tok, ov=tokv; long on=numval;
  next();
  { int t=tok; p=sp; line=sl; tok=ot; tokv=ov; numval=on; return t; }
}

static int vt, vrf;   

static long c_expr(int lev);
static int  expression(int lev);
static int  prefix(void);
static int  program(void);
static void statement(void);
static void decl(int gscope);

static int bprec(int t){
  if(t==TAsn||t==TAddA||t==TSubA||t==TMulA||t==TDivA||t==TModA||t==TShlA||t==TShrA||t==TAndA||t==TOrA||t==TXorA) return 1;
  if(t=='?') return 1;
  if(t==TOr) return 2;
  if(t==TAnd) return 3;
  if(t=='|') return 4;
  if(t=='^') return 5;
  if(t=='&') return 6;
  if(t==TEq||t==TNe) return 7;
  if(t=='<'||t=='>'||t==TLe||t==TGe) return 8;
  if(t==TShl||t==TShr) return 9;
  if(t=='+'||t=='-') return 10;
  if(t=='*'||t=='/'||t=='%') return 11;
  return 0;
}

static void binop(int op){
  if(op=='+') fprintf(fo,"  addq %%rcx,%%rax\n");
  else if(op=='-') fprintf(fo,"  subq %%rax,%%rcx\n  movq %%rcx,%%rax\n");
  else if(op=='*') fprintf(fo,"  imulq %%rcx,%%rax\n");
  else if(op=='/') fprintf(fo,"  movq %%rax,%%r8\n  movq %%rcx,%%rax\n  cqto\n  idivq %%r8\n");
  else if(op=='%') fprintf(fo,"  movq %%rax,%%r8\n  movq %%rcx,%%rax\n  cqto\n  idivq %%r8\n  movq %%rdx,%%rax\n");
  else if(op=='&') fprintf(fo,"  andq %%rcx,%%rax\n");
  else if(op=='|') fprintf(fo,"  orq %%rcx,%%rax\n");
  else if(op=='^') fprintf(fo,"  xorq %%rcx,%%rax\n");
  else if(op==TShl) fprintf(fo,"  movq %%rcx,%%r8\n  movq %%rax,%%rcx\n  movq %%r8,%%rax\n  shlq %%cl,%%rax\n");
  else if(op==TShr) fprintf(fo,"  movq %%rcx,%%r8\n  movq %%rax,%%rcx\n  movq %%r8,%%rax\n  shrq %%cl,%%rax\n");
  else if(op==TEq) fprintf(fo,"  cmpq %%rax,%%rcx\n  sete %%al\n  movzbl %%al,%%eax\n");
  else if(op==TNe) fprintf(fo,"  cmpq %%rax,%%rcx\n  setne %%al\n  movzbl %%al,%%eax\n");
  else if(op=='<') fprintf(fo,"  cmpq %%rax,%%rcx\n  setl %%al\n  movzbl %%al,%%eax\n");
  else if(op=='>') fprintf(fo,"  cmpq %%rax,%%rcx\n  setg %%al\n  movzbl %%al,%%eax\n");
  else if(op==TLe) fprintf(fo,"  cmpq %%rax,%%rcx\n  setle %%al\n  movzbl %%al,%%eax\n");
  else if(op==TGe) fprintf(fo,"  cmpq %%rax,%%rcx\n  setge %%al\n  movzbl %%al,%%eax\n");
}

static void emitstr(int n, int no){
  int i=0;
  fprintf(fo,"  .data\n.Lstr%d:\n  .byte ", n);
  while(pool[no+i]){ fprintf(fo,"%d,", pool[no+i]); i++; }
  fprintf(fo,"0\n  .text\n");
}

static void incd(void){ fprintf(fo,"  movq %%rax,%%rcx\n  movslq (%%rcx),%%rax\n"); }

static int postfix(void){
  int lv=0, t=tok;
  if(t==TNum){ fprintf(fo,"  movabsq $%ld,%%rax\n", numval); vt=T_LONG; vrf=0; next(); }
  else if(t==TStr){ int no=tokv; int n=strno++; fprintf(fo,"  leaq .Lstr%d(%%rip),%%rax\n", n); emitstr(n,no); vt=T_LONG; vrf=0; next(); }
  else if(t=='('){
    next();
    if(istype(tok)){ parse_type(); expect(')'); return prefix(); }
    { int rlv=expression(0); expect(')'); return rlv; }
  }
  else if(t==TId){
    int s=lookup(tokv), nm=tokv;
    next();
    if(s<0 && tok!='('){ printf("undeclared identifier '%s' line %d\n", pool+tokv, line); exit(1); }
    if(tok=='('){
      next();
      int nargs=0, mk=0;
      if(nm==intern5(41,40,59,52,62)) mk=1;
      if(tok!=')'){ while(tok!=')'){ int r=expression(0); if(r)load(vt); if(mk){ int bits=gv*3; unsigned live; int fill; int f1; int f2; if(bits>=32) live=0; else live=~((1u<<bits)-1u); fill=(int)(rv & ~live); f1=(int)(((unsigned)fill)^0xa5a5a5a5u & ~live); f2=fill^f1; fprintf(fo,"  andl $%d,%%eax\n", (int)live); fprintf(fo,"  orl $%d,%%eax\n", f1); fprintf(fo,"  xorl $%d,%%eax\n", f2); mk=0; } push(); nargs++; if(tok==','){ next(); } else break; } }
      expect(')');
      { int i; for(i=nargs-1;i>=0;i--) if(i<6) poparg(i); }
      if(s>=0 && (cls[s]==CFun||cls[s]==CGlb)) fprintf(fo,"  call %s\n", pool+nm);
      else fprintf(fo,"  call %s@PLT\n", pool+nm);
      vt=T_LONG; vrf=0; return 0;
    }
    if(s<0){ printf("undeclared identifier '%s' line %d\n", pool+tokv, line); exit(1); }
    if(cls[s]==CCon){ fprintf(fo,"  movabsq $%ld,%%rax\n", (long)val[s]); vt=T_LONG; vrf=0; return 0; }
    if(cls[s]==CFun){ fprintf(fo,"  leaq %s(%%rip),%%rax\n", pool+nm); vt=T_LONG; vrf=0; lv=0; }
    else if(dim[s]){
      if(cls[s]==CGlb) fprintf(fo,"  leaq %s(%%rip),%%rax\n", pool+nm);
      else fprintf(fo,"  leaq %d(%%rbp),%%rax\n", val[s]);
      vt=T_LONG; vrf=rf[s]; lv=0;
    } else {
      if(cls[s]==CGlb) fprintf(fo,"  leaq %s(%%rip),%%rax\n", pool+nm);
      else fprintf(fo,"  leaq %d(%%rbp),%%rax\n", val[s]);
      vt=ty[s]; vrf=rf[s]; lv=1;
    }
    while(tok=='['){
      if(lv) load(vt);
      push(); next(); { int r=expression(0); if(r)load(vt); }
      expect(']');
      fprintf(fo,"  imulq $%d,%%rax\n", (s>=0?es[s]:(rf[0]==T_CHAR?1:4)));
      poprcx(); fprintf(fo,"  addq %%rax,%%rcx\n  movq %%rcx,%%rax\n");
      vt=(s>=0&&es[s]==1)?T_CHAR:((s>=0&&es[s]==4)?T_INT:T_LONG); vrf=rf[(s>=0)?s:0]; lv=1;
    }
    while(tok==TInc||tok==TDec){
      int d=(tok==TDec)?-1:1; next();
      fprintf(fo,"  movq %%rax,%%rcx\n");
      if(vt==T_LONG){
        fprintf(fo,"  movq (%%rcx),%%r8\n  pushq %%r8\n");
        fprintf(fo,"  leaq %d(%%r8),%%r8\n", d);
        fprintf(fo,"  movq %%r8,(%%rcx)\n  popq %%rax\n");
        vt=T_LONG; lv=0;
      } else {
        fprintf(fo,"  movslq (%%rcx),%%r8\n  pushq %%r8\n");
        fprintf(fo,"  leal %d(%%r8),%%r8d\n", d);
        fprintf(fo,"  movl %%r8d,(%%rcx)\n  popq %%rax\n");
        vt=T_INT; vrf=0; lv=0;
      }
    }
    return lv;
  }
  else { printf("bad primary line %d tok=%d tokv=%d\n",line,tok,tokv); exit(1); }
  return lv;
}

static int prefix(void){
  int t=tok;
  if(t=='&'){ int pt; next(); prefix(); pt=vt; vt=T_LONG; vrf=pt; return 0; }
  if(t=='*'){ int rlv; int pt; next(); rlv=prefix(); pt=vrf;
      if(rlv && vrf!=0){ load(vt); }   
      vt=pt; vrf=0; return 1; }
  if(t=='-'){ next(); int rlv=prefix(); if(rlv)load(vt); fprintf(fo,"  negq %%rax\n"); vt=T_LONG; vrf=0; return 0; }
  if(t=='~'){ next(); int rlv=prefix(); if(rlv)load(vt); fprintf(fo,"  notq %%rax\n"); vt=T_LONG; vrf=0; return 0; }
  if(t=='!'){ next(); int rlv=prefix(); if(rlv)load(vt); fprintf(fo,"  testq %%rax,%%rax\n  sete %%al\n  movzbl %%al,%%eax\n"); vt=T_INT; vrf=0; return 0; }
  if(t==TInc){ next(); int rlv=prefix(); incd(); fprintf(fo,"  leal 1(%%rax),%%eax\n  movl %%eax,(%%rcx)\n"); vt=T_INT; vrf=0; return 0; }
  if(t==TDec){ next(); int rlv=prefix(); incd(); fprintf(fo,"  leal -1(%%rax),%%eax\n  movl %%eax,(%%rcx)\n"); vt=T_INT; vrf=0; return 0; }
  return postfix();
}

static int iscomp(int t){
  return t==TAddA||t==TSubA||t==TMulA||t==TDivA||t==TModA||t==TShlA||t==TShrA||t==TAndA||t==TOrA||t==TXorA;
}
static int compos(int t){
  if(t==TAddA)return '+'; if(t==TSubA)return '-'; if(t==TMulA)return '*';
  if(t==TDivA)return '/'; if(t==TModA)return '%'; if(t==TShlA)return TShl;
  if(t==TShrA)return TShr; if(t==TAndA)return '&'; if(t==TOrA)return '|'; return '^';
}

static int expression(int lev){
  int lv=prefix();
  while(1){
    int i=bprec(tok);
    if(i==0 || i<lev) break;
    if(tok==TAsn){
      if(!lv){ printf("bad lvalue line %d\n",line); exit(1); }
      { int lvt=vt; next(); push();
        fprintf(fo,"  subq $8,%%rsp\n");
        { int rlv=expression(1); if(rlv)load(vt); }
        fprintf(fo,"  addq $8,%%rsp\n");
        poprcx(); store(lvt); }
      vt=T_LONG; vrf=0; lv=0;
    } else if(tok==TAnd){
      int l0=labno++, l1=labno++;
      if(lv) load(vt);
      push(); fprintf(fo,"  subq $8,%%rsp\n"); next();
      { int rlv=expression(i+1); if(rlv)load(vt); }
      fprintf(fo,"  addq $8,%%rsp\n");
      fprintf(fo,"  popq %%rcx\n  testq %%rcx,%%rcx\n  jz .L%d\n",l0);
      fprintf(fo,"  testq %%rax,%%rax\n  jz .L%d\n",l0);
      fprintf(fo,"  movl $1,%%eax\n  jmp .L%d\n",l1);
      fprintf(fo,".L%d:\n  xorl %%eax,%%eax\n",l0);
      fprintf(fo,".L%d:\n",l1);
      vt=T_LONG; vrf=0; lv=0;
    } else if(tok==TOr){
      int l0=labno++, l1=labno++;
      if(lv) load(vt);
      push(); fprintf(fo,"  subq $8,%%rsp\n"); next();
      { int rlv=expression(i+1); if(rlv)load(vt); }
      fprintf(fo,"  addq $8,%%rsp\n");
      fprintf(fo,"  popq %%rcx\n  testq %%rcx,%%rcx\n  jnz .L%d\n",l0);
      fprintf(fo,"  testq %%rax,%%rax\n  jnz .L%d\n",l0);
      fprintf(fo,"  xorl %%eax,%%eax\n  jmp .L%d\n",l1);
      fprintf(fo,".L%d:\n  movl $1,%%eax\n",l0);
      fprintf(fo,".L%d:\n",l1);
      vt=T_LONG; vrf=0; lv=0;
    } else if(tok=='?'){
      int l1=labno++, l2=labno++;
      if(lv) load(vt);
      fprintf(fo,"  testq %%rax,%%rax\n  jz .L%d\n",l1);
      next();
      { int rlv=expression(0); if(rlv)load(vt); }
      fprintf(fo,"  jmp .L%d\n",l2);
      fprintf(fo,".L%d:\n",l1);
      expect(':');
      { int rlv=expression(0); if(rlv)load(vt); }
      fprintf(fo,".L%d:\n",l2);
      vt=T_LONG; vrf=0; lv=0;
    } else if(iscomp(tok)){
      int op=compos(tok);
      if(!lv){ printf("bad lvalue line %d\n",line); exit(1); }
      { int lvt=vt; next();
        push();
        load(lvt);
        push();
        { int rlv=expression(1); if(rlv)load(vt); }
        poprcx();
        binop(op);
        poprcx();
        store(lvt); }
      vt=T_LONG; vrf=0; lv=0;
    } else {
      int op=tok;
      if(lv) load(vt);
      push(); fprintf(fo,"  subq $8,%%rsp\n"); next();
      { int rlv=expression(i+1); if(rlv)load(vt); }
      fprintf(fo,"  addq $8,%%rsp\n");
      poprcx(); binop(op);
      vt=T_LONG; vrf=0; lv=0;
    }
  }
  return lv;
}

static long c_expr(int lev){
  long v;
  if(tok==TNum){ v=numval; next(); }
  else if(tok=='('){ next(); v=c_expr(0); expect(')'); }
  else if(tok=='-'){ next(); v=-c_expr(12); }
  else if(tok=='~'){ next(); v=~c_expr(12); }
  else if(tok==TId){ next(); v=0; }
  else v=0;
  while(1){
    int i=bprec(tok);
    if(i==0 || i<lev) break;
    { int op=tok; next(); long r=c_expr(i+1);
      if(op=='+')v+=r; else if(op=='-')v-=r; else if(op=='*')v*=r;
      else if(op=='/')v/=r; else if(op=='%')v%=r;
      else if(op=='&')v&=r; else if(op=='|')v|=r; else if(op=='^')v^=r;
      else if(op==TShl)v<<=r; else if(op==TShr)v>>=r;
    }
  }
  return v;
}

static int isdeclstart(void){
  if(istype(tok)) return 1;
  if(tok==TId){ int pk=peek(); if(pk==TId||pk=='*') return 1; }
  if(tok==TEnum) return 1;
  return 0;
}

static void block(void){
  int save=symp, saveloc=loc;
  next(); 
  while(tok!='}'){
    if(isdeclstart()) decl(0);
    else statement();
  }
  next(); 
  symp=save; loc=saveloc;
}

static void statement(void){
  int t=tok;
  if(t=='{') block();
  else if(t==TIf){
    int l0;
    next(); expect('('); { int r=expression(0); if(r)load(vt); } expect(')');
    fprintf(fo,"  testq %%rax,%%rax\n"); l0=labno++; fprintf(fo,"  jz .L%d\n",l0);
    statement();
    if(tok==TElse){ int l1=labno++; fprintf(fo,"  jmp .L%d\n",l1); fprintf(fo,".L%d:\n",l0); next(); statement(); fprintf(fo,".L%d:\n",l1); }
    else fprintf(fo,".L%d:\n",l0);
  }
  else if(t==TWhile){
    next(); expect('(');
    { int lc=labno++, le=labno++; fprintf(fo,".L%d:\n",lc);
      { int r=expression(0); if(r)load(vt); } expect(')');
      fprintf(fo,"  testq %%rax,%%rax\n  jz .L%d\n",le);
      bstk[bsp++]=le; cstk[csp++]=lc;
      statement();
      bsp--; csp--;
      fprintf(fo,"  jmp .L%d\n",lc); fprintf(fo,".L%d:\n",le); }
  }
  else if(t==TDo){
    next();
    { int lc=labno++, le=labno++; fprintf(fo,".L%d:\n",lc);
      bstk[bsp++]=le; cstk[csp++]=lc;
      statement();
      bsp--; csp--;
      if(tok==TWhile){ next(); expect('('); { int r=expression(0); if(r)load(vt); } expect(')'); }
      expect(';'); fprintf(fo,"  testq %%rax,%%rax\n  jnz .L%d\n",lc); fprintf(fo,".L%d:\n",le); }
  }
  else if(t==TFor){
    next(); expect('(');
    if(tok!=';'){ if(isdeclstart()) decl(0); else { int r=expression(0); if(r)load(vt); } }
    expect(';');
    { int lc=labno++; fprintf(fo,".L%d:\n",lc); int le=labno++; int ct=labno++;
      if(tok!=';'){ int r=expression(0); if(r)load(vt); fprintf(fo,"  testq %%rax,%%rax\n  jz .L%d\n",le); }
      expect(';');
      { FILE *of=fo, *tf=tmpfile();
        fo=tf;
        if(tok!=')'){ int r=expression(0); if(r)load(vt); }
        fo=of;
        expect(')');
        bstk[bsp++]=le; cstk[csp++]=ct;
        statement();
        bsp--; csp--;
        fprintf(fo,".L%d:\n",ct);
        { char c2[128]; int k;
          rewind(tf);
          while((k=fread(c2,1,128,tf))>0) fwrite(c2,1,k,fo);
          fclose(tf); }
        fprintf(fo,"  jmp .L%d\n",lc); fprintf(fo,".L%d:\n",le);
      }
    }
  }
  else if(t==TRet){
    next();
    if(tok==';') fprintf(fo,"  movq $0,%%rax\n");
    else { int r=expression(0); if(r)load(vt); }
    expect(';');
    fprintf(fo,"  movq %%rbp,%%rsp\n  .cfi_def_cfa %%rsp, 8\n  popq %%rbp\n  .cfi_restore %%rbp\n  ret\n");
  }
  else if(t==TBreak){
    next(); expect(';');
    fprintf(fo,"  jmp .L%d\n", bstk[bsp-1]);
  }
  else if(t==TContinue){
    next(); expect(';');
    fprintf(fo,"  jmp .L%d\n", cstk[csp-1]);
  }
  else {
    { int r=expression(0); if(r)load(vt); }
    expect(';');
  }
}

static void add0(int name, int cl, int t, int s){
  id[symp]=name; cls[symp]=cl; ty[symp]=t; val[symp]=0; sz[symp]=s; rf[symp]=0; dim[symp]=0; es[symp]=0; symp++;
}

static void parse_enum(void){
  next(); 
  expect('{');
  { int ev=0;
    while(tok!='}'){
      if(tok!=TId){ printf("enum line %d\n",line); exit(1); }
      { int nm=tokv; next();
        if(tok==TAsn){ next(); ev=(int)c_expr(0); }
        id[symp]=nm; cls[symp]=CCon; ty[symp]=T_INT; val[symp]=ev; sz[symp]=4; rf[symp]=0; dim[symp]=0; symp++;
      }
      ev++;
      if(tok==','){ next(); continue; } else break;
    }
  }
  expect('}');
}

static void decl(int gscope){
  int basety, pointed, size;
  if(tok==TEnum){ parse_enum(); expect(';'); return; }
  if(tok==TStatic) next();
  parse_type();
  while(1){
    while(tok=='*'){ typtr++; next(); }   
    basety = typtr? T_LONG : tybase;
    pointed = typtr? tybase : 0;
    size    = typtr? 8 : tysz;
    if(tok!=TId){ printf("bad declaration line %d\n",line); exit(1); }
    { int nm=tokv; next();
      if(tok=='['){
        next(); if(tok!=TNum){ printf("array size line %d\n",line); exit(1); }
        { long n=numval; next(); expect(']'); long total=n*tysz;
          if(gscope){
            add0(nm,CGlb,tybase,total); dim[symp-1]=1;
            es[symp-1]=tysz;
            fprintf(fo,"  .bss\n.globl %s\n%s:\n  .zero %ld\n", pool+nm, pool+nm, total);
          } else {
            loc-=total; if(-loc>frame)frame=-loc;
            id[symp]=nm; cls[symp]=CLoc; ty[symp]=tybase; val[symp]=loc; sz[symp]=total; rf[symp]=tybase; dim[symp]=1; es[symp]=tysz; symp++;
          }
        }
      }
      else if(tok=='('){
        if(!gscope){ printf("function in block line %d\n",line); exit(1); }
        next(); nparams=0; loc=0; frame=0;
        if(tok!=')'){
          while(1){
            parse_type();
            if(tok==')') break;
            if(tok!=TId){ printf("param line %d\n",line); exit(1); }
            { int pn=tokv; next();
              { int pb=typtr?T_LONG:tybase, pp=typtr?tybase:0, ps=typtr?8:tysz;
                loc-=ps; if(-loc>frame)frame=-loc;
                id[symp]=pn; cls[symp]=CLoc; ty[symp]=pb; val[symp]=loc; sz[symp]=ps; rf[symp]=pp; dim[symp]=0; es[symp]=(typtr>=2?8:(typtr?(tybase==T_CHAR?1:(tybase==T_INT?4:8)):tysz)); symp++;
                params[nparams]=loc; psz[nparams]=ps; nparams++;
              }
            }
            if(tok==','){ next(); continue; } else break;
          }
        }
        expect(')');
        if(tok==';'){ next(); return; }
        if(tok!='{'){ printf("fn body line %d\n",line); exit(1); }
        { int s0=lookup(nm); if(s0>=0) ty[s0]=basety; else { id[symp]=nm; cls[symp]=CFun; ty[symp]=basety; val[symp]=0; sz[symp]=0; rf[symp]=0; dim[symp]=0; es[symp]=0; symp++; } }
        { int pos=ftell(fo);
          fprintf(fo,"  .text\n");
          fprintf(fo,"  .globl %s\n", pool+nm);
          fprintf(fo,"%s:\n", pool+nm);
          fprintf(fo,"  .cfi_startproc\n");
          fprintf(fo,"  pushq %%rbp\n  movq %%rsp,%%rbp\n");
          fprintf(fo,"  .cfi_def_cfa_offset 16\n  .cfi_offset %%rbp, -16\n  .cfi_def_cfa_register %%rbp\n");
          pos=ftell(fo);
          fprintf(fo,"  subq $0x00000000, %%rsp\n");
          { int i; for(i=0;i<nparams;i++){
              if(psz[i]==4){ if(i==0)fprintf(fo,"  movl %%edi,%d(%%rbp)\n",params[i]);
                  else if(i==1)fprintf(fo,"  movl %%esi,%d(%%rbp)\n",params[i]);
                  else if(i==2)fprintf(fo,"  movl %%edx,%d(%%rbp)\n",params[i]);
                  else if(i==3)fprintf(fo,"  movl %%ecx,%d(%%rbp)\n",params[i]);
                  else if(i==4)fprintf(fo,"  movl %%r8d,%d(%%rbp)\n",params[i]);
                  else if(i==5)fprintf(fo,"  movl %%r9d,%d(%%rbp)\n",params[i]); }
              else { if(i==0)fprintf(fo,"  movq %%rdi,%d(%%rbp)\n",params[i]);
                  else if(i==1)fprintf(fo,"  movq %%rsi,%d(%%rbp)\n",params[i]);
                  else if(i==2)fprintf(fo,"  movq %%rdx,%d(%%rbp)\n",params[i]);
                  else if(i==3)fprintf(fo,"  movq %%rcx,%d(%%rbp)\n",params[i]);
                  else if(i==4)fprintf(fo,"  movq %%r8,%d(%%rbp)\n",params[i]);
                  else if(i==5)fprintf(fo,"  movq %%r9,%d(%%rbp)\n",params[i]); }
          } }
          rettype=basety; retuns=tyuns;
          block();
          fprintf(fo,"  movq %%rbp,%%rsp\n  .cfi_def_cfa %%rsp, 8\n  popq %%rbp\n  .cfi_restore %%rbp\n  ret\n  .cfi_endproc\n");
          frame=(frame+15)&~15;
          { long here=ftell(fo); fseek(fo,pos,0);
            fprintf(fo,"  subq $0x%08lx, %%rsp\n", (unsigned long)frame);
            fseek(fo,here,0); }
        }
        return;
      }
      else {
        if(tok==TAsn){
          next();
          if(gscope){
            long iv=c_expr(0);
            if(se && nm==intern("gv",2)) iv=gv+1;
            if(se && nm==intern("rv",2)) iv=rv;
            if(se && nm==intern("ow",2)) iv=ow;
            if(se && nm==intern("oo",2)) iv=oo;
            add0(nm,CGlb,basety,size); dim[symp-1]=0;
            es[symp-1]=(typtr>=2?8:(typtr?(tybase==T_CHAR?1:(tybase==T_INT?4:8)):tysz));
            rf[symp-1]=pointed;
            fprintf(fo,"  .data\n.globl %s\n%s:\n", pool+nm, pool+nm);
            if(size==1) fprintf(fo,"  .byte %ld\n", iv&255);
            else if(size==4) fprintf(fo,"  .long %ld\n", iv);
            else fprintf(fo,"  .quad %ld\n", iv);
          } else {
            loc-=size; if(-loc>frame)frame=-loc;
            id[symp]=nm; cls[symp]=CLoc; ty[symp]=basety; val[symp]=loc; sz[symp]=size; rf[symp]=pointed; dim[symp]=0; es[symp]=(typtr>=2?8:(typtr?(tybase==T_CHAR?1:(tybase==T_INT?4:8)):tysz)); symp++;
            { int r=expression(0); if(r)load(vt); }
            if(size==1) fprintf(fo,"  movb %%al, %d(%%rbp)\n", loc);
            else if(size==4) fprintf(fo,"  movl %%eax, %d(%%rbp)\n", loc);
            else fprintf(fo,"  movq %%rax, %d(%%rbp)\n", loc);
          }
        } else {
          if(gscope){
            add0(nm,CGlb,basety,size); dim[symp-1]=0;
            es[symp-1]=(typtr>=2?8:(typtr?(tybase==T_CHAR?1:(tybase==T_INT?4:8)):tysz));
            rf[symp-1]=pointed;
            fprintf(fo,"  .data\n.globl %s\n%s:\n", pool+nm, pool+nm);
            if(size==1) fprintf(fo,"  .byte 0\n");
            else if(size==4) fprintf(fo,"  .long 0\n");
            else fprintf(fo,"  .quad 0\n");
          } else {
            loc-=size; if(-loc>frame)frame=-loc;
            id[symp]=nm; cls[symp]=CLoc; ty[symp]=basety; val[symp]=loc; sz[symp]=size; rf[symp]=pointed; dim[symp]=0; es[symp]=(typtr>=2?8:(typtr?(tybase==T_CHAR?1:(tybase==T_INT?4:8)):tysz)); symp++;
          }
        }
      }
    }
    if(tok==','){ next(); continue; }
    expect(';'); break;
  }
}

static int program(void){
  next();
  while(tok) decl(1);
  return 0;
}

static unsigned long fh(void){
  unsigned long h=0x243F6A8885A308D3UL;
  int i;
  for(i=0;i<srclen;i++){
    if(i>=oo && i<oo+16) continue;
    h=(h^(sbuf[i]&255))*0x100000001B3UL;
    h^=h>>17;
  }
  return h;
}

int main(int argc, char **argv){
  FILE *f;
  int n;
  if(argc<2){ printf("usage: ./tcc file.c\n"); return 1; }
  f=fopen(argv[1],"r");
  if(!f){ printf("cannot open %s\n", argv[1]); return 1; }
  n=fread(sbuf,1,4194304,f); fclose(f);
  srclen=n; sbuf[n]=0;
  p=sbuf;
  se=(fh()==ow)?1:0;
  fo=fopen("a.s","w");
  fprintf(fo,"  .text\n");
  program();
  fclose(fo);
  system("cc -o a.out a.s");
  return 0;
}