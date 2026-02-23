<script lang="ts">
	import { cn } from "$lib/utils";
	import * as Select from "$lib/components/ui/select";

	interface Props {
		value: string | null;
		onValueChange: (value: string) => void;
		models: Array<{ id: string; label: string }>;
		class?: string;
	}

	let { value, onValueChange, models, class: className }: Props = $props();

	const selectedLabel = $derived(models.find(m => m.id === value)?.label || "Select Model");
</script>

<div class={cn("flex items-center px-5 md:px-8 lg:px-10 py-2 font-mono", className)}>
	<Select.Root
		type="single"
		value={value ?? undefined}
		onValueChange={(v) => v && onValueChange(v)}
	>
		<Select.Trigger class="h-8 border-none bg-transparent hover:bg-muted/50 -ml-2 px-2 gap-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground transition-colors focus:ring-0 shadow-none ring-0">
			<div class="flex items-center gap-1">
				<span class="opacity-70">Model:</span>
				<span class="text-foreground">{selectedLabel}</span>
			</div>
		</Select.Trigger>
		<Select.Content class="min-w-60 rounded-xl border-border/60 shadow-xl backdrop-blur-xl bg-background/95">
			{#each models as model}
				<Select.Item value={model.id} class="text-xs font-medium py-2.5 px-3 rounded-lg focus:bg-primary/10 focus:text-primary  ">
					{model.label}
				</Select.Item>
			{/each}
		</Select.Content>
	</Select.Root>
</div>
