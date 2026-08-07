BITS 16
ORG 0x7C00


start:
    cli

    ; initialize segment
    xor ax, ax
    mov ds, ax
    mov es, ax

    ; set stack
    mov ss, ax
    mov sp, 0x7C00

    sti


    ; cls
    mov ax, 0x0003
    int 0x10


    ; print ASCII
    mov si, art

print:
    lodsb
    cmp al, 0
    je idle

    mov ah, 0x0E
    mov bh, 0x00
    int 0x10

    jmp print


idle:
    ; OS idle status
    cli
    hlt
    jmp idle



art:
    db 13,10
    db "        /\_/\ ",13,10
    db "       (> w <) ",13,10
    db "        /_ _\ ",13,10
    db 13,10
    db "    simple x86 OS",13,10
    db "    Boot Success!",13,10
    db 13,10
    db "    CPU: Intel x86",13,10
    db "    By: ulsidae",13,10
    db 0



; 512 byte boot sector
times 510-($-$$) db 0

; boot signature
dw 0xAA55
