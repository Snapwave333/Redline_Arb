using CalmCadence.Core.Enums;
using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class TaskItemConfiguration : IEntityTypeConfiguration<TaskItem>
{
    public void Configure(EntityTypeBuilder<TaskItem> builder)
    {
        builder.ToTable("Tasks");
        builder.HasKey(t => t.Id);

        builder.Property(t => t.Title).IsRequired().HasMaxLength(500);
        builder.Property(t => t.Notes).HasMaxLength(4000);
        builder.Property(t => t.Priority).HasConversion<int>();
        builder.Property(t => t.Status).HasConversion<int>();
        builder.Property(t => t.OrderIndex).HasDefaultValue(0);
        builder.Property(t => t.CreatedAt).IsRequired();
        builder.Property(t => t.UpdatedAt).IsRequired();
        builder.Property(t => t.IsArchived).HasDefaultValue(false);

        builder.HasIndex(t => new { t.Status, t.Priority });
        builder.HasIndex(t => t.DueAt);
    }
}
