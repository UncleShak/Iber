import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

/* All status colour goes through these tokens - never a hex in a component. */
const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap [&_svg]:size-3.5 [&_svg]:shrink-0',
  {
    variants: {
      status: {
        red: 'bg-rag-red-bg text-rag-red border-rag-red/25',
        amber: 'bg-rag-amber-bg text-rag-amber border-rag-amber/25',
        green: 'bg-rag-green-bg text-rag-green border-rag-green/25',
        grey: 'bg-rag-grey-bg text-rag-grey border-rag-grey/25'
      }
    },
    defaultVariants: { status: 'grey' }
  }
)

type BadgeProps = React.ComponentProps<'span'> & VariantProps<typeof badgeVariants>

function Badge({ className, status, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ status }), className)} {...props} />
}

export { Badge, badgeVariants }
