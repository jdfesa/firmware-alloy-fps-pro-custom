/* SPDX-License-Identifier: GPL-2.0-or-later */
.syntax unified
.cpu cortex-m0
.thumb
.section .text.exception_proxy,"ax",%progbits
.global exception_proxy
.type exception_proxy,%function
.thumb_func
exception_proxy:
    mrs r0, ipsr
    lsls r0, r0, #2
    movs r1, #128
    lsls r1, r1, #2
    ldr r0, [r1, r0]
    bx r0
.size exception_proxy, .-exception_proxy

.section .text.jump_application,"ax",%progbits
.global jump_application
.type jump_application,%function
.thumb_func
jump_application:
    movs r0, #128
    lsls r0, r0, #2
    ldr r1, [r0, #4]
    ldr r0, [r0]
    msr msp, r0
    bx r1
.size jump_application, .-jump_application
