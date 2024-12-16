import { Notyf } from 'notyf'

// Use Notyf to show notifications
export const notyf = new Notyf({
	duration: 4500,
	dismissible: true,
	position: {
		x: 'right',
		y: 'top'
	}
})
