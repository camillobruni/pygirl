	.type	main, @function
main:
	;; cmovCOND tests.
	pushl	%ebx
	movl	12(%esp), %ebx
	cmove	16(%esp), %ebx
	cmovge	20(%esp), %ebx
	movl	24(%esp), %eax
	cmovs	%eax, %ebx
	call	foobar
	;; expected {4(%esp) | (%esp), %esi, %edi, %ebp | %ebx}
#APP
	/* GCROOT %ebx */
#NO_APP
	popl	%ebx
	ret

	.size	main, .-main
