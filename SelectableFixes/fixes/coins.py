"""One-time top-up, per save: keep larger balances and permit normal spending."""
from lua_chunk import Assembler
NAME='coins'
MARKER='__seasons_selectable_fixes_coins_v1'
def apply(ctx,options):
 p=ctx.proto('scripts/settingsWrapper.lua','root.277',params=1,nup=1)
 a=Assembler();a.emit('GETUPVAL',1,0);a.get(2,1,'IngameCurrencyAmount')
 a.emit('TEST',2,0,1);a.jmp('amount_ready');a.load(2,0.0);a.label('amount_ready')
 a.get(3,1,MARKER);a.emit('TEST',3,0,0);a.jmp('grant');a.jmp('done')
 a.label('grant');a.load(4,float(options['coins_amount']));a.emit('LT',0,2,4);a.jmp('mark')
 a.emit('MOVE',2,4);a.set(1,'IngameCurrencyAmount',2)
 a.label('mark');a.emit('LOADBOOL',3,1);a.set(1,MARKER,3)
 a.label('done');a.emit('RETURN',2,2);a.finish(p)
