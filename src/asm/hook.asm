; Dune CD Korean hook segment  (CS = this segment, entered via far call)
; Game DS on entry. AL = character.
bits 16
org 0
%include "tables.inc"     ; defines NT, LEADTAB, TRAILTAB(128 each), G9L, G9R, G7

lastlead:  db 0
blitptr:   dd 0

; ---------------- big font (replaces 0xD096) ----------------

big_draw:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push es
    xor ah,ah
    mov si,ax
    mov bl,[cs:leadtab+si]
    cmp bl,0xff
    je .notlead
    mov [cs:lastlead],bl
    jmp .done
.notlead:
    mov bl,[cs:trailtab+si]
    cmp bl,0xff
    jne .hangul
    ; ---- original behaviour ----
    mov si,ax
    shl si,1
    shl si,1
    shl si,1
    add si,ax
    add si,[0x2514]
    mov bx,0xceec
    xlatb
    mov dx,[0xd82c]
    mov bx,[0xd82e]
    add [0xd82c],ax
    mov cl,al
    mov ch,9
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    call far [0x38d1]
    jmp .done
.hangul:
    xor bh,bh
    mov al,[cs:lastlead]
    mov ah,NT
    mul ah
    add ax,bx                 ; syllable index
    mov si,ax
    shl si,1
    shl si,1
    shl si,1
    add si,ax                 ; *9
    mov di,[0x38d1]
    mov [cs:blitptr],di
    mov di,[0x38d3]
    mov [cs:blitptr+2],di
    mov dx,[0xd82c]
    mov bx,[0xd82e]
    mov bp,sp
    cmp bx,150                ; upper screen: dialogue subtitles -> Dalmoori 8px
    jae .lower
    cmp word [ss:bp+20],0xd1cf   ; simple string printer (map tooltip etc.) -> 7px menu font
    je .menu7
    jmp .dal
.lower:
    cmp word [ss:bp+20],0x8c45   ; lower screen via text layout loop (intro text) -> Galmuri 9px
    je .big9
.menu7:
    ; ---- menu / UI: 7px glyph, advance 8 ----
    add word [0xd82c],8
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    push ds
    push cs
    pop ds
    add si,g7b
    mov cx,0x0908
    call far [cs:blitptr]
    pop ds
    jmp .done
.dal:
    ; ---- dialogue: Dalmoori 8x8, advance 10 ----
    add word [0xd82c],10
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    push ds
    push cs
    pop ds
    add si,gd
    mov cx,0x0908
    call far [cs:blitptr]
    pop ds
    jmp .done
.big9:
    ; ---- Galmuri 9px (9 columns), advance 10 ----
    add word [0xd82c],10
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    push ds
    push cs
    pop ds
    push ax
    push bx
    push dx
    push si
    add si,g9l
    mov cx,0x0908
    call far [cs:blitptr]
    pop si
    pop dx
    pop bx
    pop ax
    add si,g9r
    add dx,8
    mov cx,0x0901
    call far [cs:blitptr]
    pop ds
.done:
    pop es
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    retf

; ---------------- small font (replaces 0xD12F) ----------------

small_draw:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push es
    xor ah,ah
    mov si,ax
    mov bl,[cs:leadtab+si]
    cmp bl,0xff
    je .notlead
    mov [cs:lastlead],bl
    jmp .done
.notlead:
    mov bl,[cs:trailtab+si]
    cmp bl,0xff
    jne .hangul
    mov si,ax
    shl si,1
    shl si,1
    shl si,1
    sub si,ax
    add si,[0x2516]
    mov bx,0xcf6c
    xlatb
    mov dx,[0xd82c]
    mov bx,[0xd82e]
    add [0xd82c],ax
    mov cl,al
    mov ch,7
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    call far [0x38d1]
    jmp .done
.hangul:
    xor bh,bh
    mov al,[cs:lastlead]
    mov ah,NT
    mul ah
    add ax,bx
    mov si,ax
    shl si,1
    shl si,1
    shl si,1
    sub si,ax                 ; *7
    add si,g7
    mov di,[0x38d1]
    mov [cs:blitptr],di
    mov di,[0x38d3]
    mov [cs:blitptr+2],di
    mov dx,[0xd82c]
    mov bx,[0xd82e]
    add word [0xd82c],8
    mov ax,[0xdbe4]
    mov es,[0xdbda]
    push ds
    push cs
    pop ds
    mov cx,0x0708
    call far [cs:blitptr]
    pop ds
.done:
    pop es
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    retf

; ---------------- line centering for lower-screen text (replaces 0x8BD1..0x8BE8) ----------------
; in: cx = words on this line, DS:SI = line text, [0xd82c] = line start x
center_line:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    cmp word [0xd82e],150       ; only text drawn in the lower screen
    jb .out
    test byte [0x4799],0x02     ; game's own centering already applied
    jnz .out
    jcxz .out
    mov bx,[0x47a0]
    xor di,di
.ch:
    lodsb
    cmp al,0x20
    je .gap
    cmp al,0x0d
    je .gap
    test al,0x80
    jnz .measured
    cmp al,0x09
    jb .ch
    xlatb
    xor ah,ah
    add di,ax
    jmp .ch
.gap:
    dec cx
    jz .measured
    add di,6
.skip:
    cmp byte [si],0x20
    je .adv
    cmp byte [si],0x0d
    jne .ch
.adv:
    inc si
    jmp .skip
.measured:
    mov ax,[0x478f]
    sub ax,di
    jle .out
    shr ax,1
    add [0xd82c],ax
.out:
    mov word [0x479c],0
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    mov dx,6
    retf
